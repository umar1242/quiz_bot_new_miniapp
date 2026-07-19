"""
routers/creator.py
FSM флоу создания квиза:
  awaiting_file → setup_title → [setup_split] → setup_timer → setup_order → setup_shuffle → confirm_save
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Document, Message
from sqlalchemy.ext.asyncio import AsyncSession

from dto.quiz_dto import QuizCreateDTO
from keyboards.creator_kb import confirm_save_kb, order_kb, shuffle_answers_kb, timer_kb, split_kb, SPLIT_THRESHOLD
from services import parser as parser_factory
from services.quiz_service import create_quiz
from utils.deeplink import make_quiz_link
from utils.formatters import fmt_parse_preview, fmt_quiz_saved
from utils.validators import validate_questions
from utils.i18n import t

router = Router()


class CreateQuiz(StatesGroup):
    awaiting_file   = State()
    setup_title     = State()   # ввод названия квиза
    setup_split     = State()   # разбивка на части (если вопросов > SPLIT_THRESHOLD)
    setup_timer     = State()
    setup_order     = State()
    setup_shuffle   = State()
    confirm_save    = State()


# ---------------------------------------------------------------------------
# Вход в флоу — пользователь отправляет файл
# ---------------------------------------------------------------------------

@router.message(F.document)
async def handle_document(message: Message, state: FSMContext, lang: str) -> None:
    doc: Document = message.document
    ext = "." + doc.file_name.rsplit(".", 1)[-1].lower() if "." in doc.file_name else ""
    supported = [".txt", ".docx", ".pdf"]
    if ext not in supported:
        await message.answer(
            t("creator.unsupported_format", lang, ext=ext, supported=", ".join(supported))
        )
        return

    await message.answer(t("creator.processing", lang))

    # Скачиваем
    bot = message.bot
    file = await bot.get_file(doc.file_id)
    buf = await bot.download_file(file.file_path)
    file_bytes = buf.read()

    # Парсим
    try:
        parser = parser_factory.get_parser(doc.file_name)
        questions = await parser.parse(file_bytes)
    except ValueError as e:
        await message.answer(f"❌ {e}")
        return

    # Валидируем
    errors = validate_questions(questions, lang)
    preview = fmt_parse_preview(len(questions), errors, lang)
    await message.answer(preview)

    if errors:
        return  # просим исправить файл

    # Сохраняем вопросы в FSM (title пока не знаем — спросим у пользователя)
    q_data = [
        {"text": q.text, "explanation": q.explanation,
         "answers": [{"text": a.text, "is_correct": a.is_correct} for a in q.answers]}
        for q in questions
    ]
    # Предлагаем имя файла как подсказку, но пользователь может ввести своё
    suggested = doc.file_name.rsplit(".", 1)[0]
    await state.update_data(questions=q_data, suggested_title=suggested)
    await state.set_state(CreateQuiz.setup_title)
    await message.answer(t("creator.ask_title", lang, suggested=suggested))





# ---------------------------------------------------------------------------
# Шаг 0а: Название квиза
# ---------------------------------------------------------------------------

@router.message(CreateQuiz.setup_title, F.text)
async def handle_title(message: Message, state: FSMContext, lang: str) -> None:
    """Принимает название квиза от пользователя."""
    data = await state.get_data()
    suggested = data.get("suggested_title", "Quiz")

    # Точка = оставить предложенное название
    raw = message.text.strip()
    title = suggested if raw == "." else raw

    if len(title) > 255:
        await message.answer(t("creator.title_too_long", lang, length=len(title)))
        return

    if not title:
        await message.answer(t("creator.title_empty", lang))
        return

    await state.update_data(title=title)
    questions = data["questions"]

    # Следующий шаг — split или timer
    if len(questions) > SPLIT_THRESHOLD:
        await state.set_state(CreateQuiz.setup_split)
        await message.answer(
            t("creator.ask_split", lang, count=len(questions)),
            reply_markup=split_kb(len(questions), lang),
        )
    else:
        await state.set_state(CreateQuiz.setup_timer)
        await message.answer(
            t("creator.ask_timer", lang, title=title),
            reply_markup=timer_kb(lang),
        )


# ---------------------------------------------------------------------------
# Шаг 0 (опциональный): разбивка на части
# ---------------------------------------------------------------------------

@router.callback_query(CreateQuiz.setup_split, F.data.startswith("split:"))
async def cb_split(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    chunk_size = int(call.data.split(":")[1])
    data = await state.get_data()
    title = data.get("title", "")
    await state.update_data(chunk_size=chunk_size)
    await state.set_state(CreateQuiz.setup_timer)
    await call.message.edit_text(
        t("creator.ask_timer", lang, title=title),
        reply_markup=timer_kb(lang),
    )

# ---------------------------------------------------------------------------
# Шаг 1: Таймер
# ---------------------------------------------------------------------------

@router.callback_query(CreateQuiz.setup_timer, F.data.startswith("timer:"))
async def cb_timer(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    timer_sec = int(call.data.split(":")[1])
    await state.update_data(timer_sec=timer_sec)
    await state.set_state(CreateQuiz.setup_order)
    await call.message.edit_text(
        t("creator.ask_order", lang, timer=timer_sec),
        reply_markup=order_kb(lang),
    )


# ---------------------------------------------------------------------------
# Шаг 2: Порядок вопросов
# ---------------------------------------------------------------------------

@router.callback_query(CreateQuiz.setup_order, F.data.startswith("order:"))
async def cb_order(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    shuffle_q = call.data.split(":")[1] == "shuffle"
    await state.update_data(shuffle_q=shuffle_q)
    await state.set_state(CreateQuiz.setup_shuffle)
    await call.message.edit_text(
        t("creator.ask_shuffle_a", lang),
        reply_markup=shuffle_answers_kb(lang),
    )


# ---------------------------------------------------------------------------
# Шаг 3: Перемешивание ответов
# ---------------------------------------------------------------------------

@router.callback_query(CreateQuiz.setup_shuffle, F.data.startswith("shuffle_a:"))
async def cb_shuffle(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    shuffle_a = call.data.split(":")[1] == "shuffle"
    await state.update_data(shuffle_a=shuffle_a)
    await state.set_state(CreateQuiz.confirm_save)

    data = await state.get_data()
    q_label = t("creator.shuffled", lang) if data["shuffle_q"] else t("creator.in_order", lang)
    a_label = t("creator.shuffled", lang) if shuffle_a else t("creator.in_order", lang)

    await call.message.edit_text(
        t("creator.summary", lang,
          count=len(data["questions"]), timer=data["timer_sec"],
          q_label=q_label, a_label=a_label),
        reply_markup=confirm_save_kb(lang),
    )


# ---------------------------------------------------------------------------
# Шаг 4: Подтверждение и сохранение
# ---------------------------------------------------------------------------

@router.callback_query(CreateQuiz.confirm_save, F.data == "save:confirm")
async def cb_save_confirm(call: CallbackQuery, state: FSMContext, db: AsyncSession, lang: str) -> None:
    data = await state.get_data()
    await state.clear()

    from dto.quiz_dto import QuestionDTO, AnswerDTO

    def _build_questions(raw_list: list) -> list[QuestionDTO]:
        return [
            QuestionDTO(
                text=q["text"],
                explanation=q.get("explanation"),
                answers=[AnswerDTO(text=a["text"], is_correct=a["is_correct"]) for a in q["answers"]]
            )
            for q in raw_list
        ]

    all_raw   = data["questions"]
    title     = data["title"]
    chunk_size = int(data.get("chunk_size", 0))

    # Разбиваем на части если пользователь выбрал chunk_size > 0
    if chunk_size > 0:
        chunks = [all_raw[i:i + chunk_size] for i in range(0, len(all_raw), chunk_size)]
    else:
        chunks = [all_raw]

    saved_quizzes = []
    for idx, chunk in enumerate(chunks, start=1):
        part_title = f"{title}_часть_{idx}" if len(chunks) > 1 else title
        dto = QuizCreateDTO(
            owner_id=call.from_user.id,
            title=part_title,
            questions=_build_questions(chunk),
            timer_sec=data["timer_sec"],
            shuffle_q=data["shuffle_q"],
            shuffle_a=data["shuffle_a"],
        )
        quiz = await create_quiz(db, dto)
        saved_quizzes.append(quiz)

    if len(saved_quizzes) == 1:
        # Один квиз — стандартное сообщение
        link = make_quiz_link(saved_quizzes[0].id)
        await call.message.edit_text(fmt_quiz_saved(saved_quizzes[0], link, lang))
    else:
        # Несколько квизов — список с ссылками
        lines = [t("creator.saved_many", lang, count=len(saved_quizzes))]
        for i, q in enumerate(saved_quizzes, start=1):
            link = make_quiz_link(q.id)
            lines.append(
                f"{i}. <b>{q.title}</b>\n"
                f"   ❓ {len(q.questions)} вопр. · /quiz_{q.id}\n"
                f"   🔗 {link}"
            )
        await call.message.edit_text("\n".join(lines))


@router.callback_query(CreateQuiz.confirm_save, F.data == "save:cancel")
async def cb_save_cancel(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await call.message.edit_text(t("creator.cancelled", lang))