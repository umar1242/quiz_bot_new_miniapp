"""
services/parser/base.py
Абстрактный базовый класс для всех парсеров.
Каждый конкретный парсер реализует только метод _to_text().
Логика разбора шаблона + = # — одна, в BaseParser.parse().
"""
import re
from abc import ABC, abstractmethod

from dto.quiz_dto import AnswerDTO, QuestionDTO

# Разделители из шаблона (классический формат — разделитель на отдельной строке)
QUESTION_SEP = re.compile(r'^\++\s*$', re.MULTILINE)   # одна или более + в строке
ANSWER_SEP   = re.compile(r'^=+\s*$',  re.MULTILINE)   # одна или более = в строке

# Разделители формата HEMIS (inline — + и = идут прямо в тексте, без новой строки)
#   +Savol matni?=#To'g'ri javob=Javob 2=Javob 3=Javob 4+
QUESTION_SEP_INLINE = re.compile(r'\++')   # одна или более + где угодно
ANSWER_SEP_INLINE   = re.compile(r'=+')    # одна или более = где угодно

CORRECT_MARK = '#'


class BaseParser(ABC):

    @abstractmethod
    async def _to_text(self, file_bytes: bytes) -> str:
        """Конвертировать файл в plain text. Реализуется в каждом парсере."""
        ...

    async def parse(self, file_bytes: bytes) -> list[QuestionDTO]:
        """
        Главный метод. Конвертирует файл → текст → список QuestionDTO.
        Бросает ValueError если формат не распознан.
        """
        text = await self._to_text(file_bytes)
        return self._parse_text(text)

    def _parse_text(self, text: str) -> list[QuestionDTO]:
        """
        Разбирает plain text по шаблону + = #.

        Поддерживаются два варианта одного и того же формата:
          1. Классический — разделители + и = стоят на отдельных строках.
          2. HEMIS (inline) — разделители + и = идут прямо в потоке текста:
             +Savol matni?=#To'g'ri javob=Javob 2=Javob 3=Javob 4+

        Сначала пробуем классический вариант (он точнее — не цепляет
        + и = внутри текста вопроса/ответа). Если вопросов не нашлось —
        пробуем inline-вариант HEMIS.
        """
        # Нормализуем переносы строк
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        questions = self._split_questions(text, QUESTION_SEP, ANSWER_SEP)
        if not questions:
            questions = self._split_questions(text, QUESTION_SEP_INLINE, ANSWER_SEP_INLINE)

        if not questions:
            raise ValueError(
                "Не удалось найти ни одного вопроса. "
                "Проверьте формат файла: вопросы разделяются знаком +, "
                "ответы — знаком =, правильный ответ начинается с #"
            )

        return questions

    @staticmethod
    def _split_questions(text: str, q_sep: re.Pattern, a_sep: re.Pattern) -> list[QuestionDTO]:
        """Разбивает текст на вопросы заданной парой разделителей."""
        questions: list[QuestionDTO] = []

        # Разбиваем на блоки вопросов по разделителю +
        for block in q_sep.split(text):
            block = block.strip()
            if not block:
                continue

            # Внутри блока разбиваем по = на части: [вопрос, ответ1, ответ2, ...]
            parts = [p.strip() for p in a_sep.split(block) if p.strip()]

            if len(parts) < 3:
                # Меньше 3 частей = вопрос + менее 2 ответов — пропускаем
                continue

            question_text = parts[0]
            answers: list[AnswerDTO] = []
            for raw in parts[1:]:
                is_correct = raw.startswith(CORRECT_MARK)
                answer_text = raw.lstrip(CORRECT_MARK).strip()
                if answer_text:
                    answers.append(AnswerDTO(text=answer_text, is_correct=is_correct))

            questions.append(QuestionDTO(text=question_text, answers=answers))

        return questions
