"""
services/flashcard_service.py
CRUD операции над Deck и Card.
Роутеры работают только через этот сервис — не трогают БД напрямую.
"""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Card, Deck
from dto.quiz_dto import DeckCreateDTO


async def create_deck(db: AsyncSession, dto: DeckCreateDTO) -> Deck:
    """Создаёт колоду с карточками из DTO. Возвращает сохранённый объект."""
    deck = Deck(owner_id=dto.owner_id, title=dto.title)
    db.add(deck)
    await db.flush()  # получаем deck.id до коммита

    for pos, c_dto in enumerate(dto.cards, start=1):
        db.add(Card(
            deck_id=deck.id,
            position=pos,
            front=c_dto.front,
            back=c_dto.back,
            back_false=c_dto.back_false,
        ))

    return await get_deck(db, deck.id)


async def get_deck(db: AsyncSession, deck_id: int) -> Deck | None:
    """Загружает колоду со всеми карточками (eager load)."""
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.cards))
    )
    return result.scalar_one_or_none()


async def get_user_decks(db: AsyncSession, owner_id: int) -> list[Deck]:
    """Список колод пользователя (с карточками для подсчёта)."""
    result = await db.execute(
        select(Deck)
        .where(Deck.owner_id == owner_id)
        .order_by(Deck.created_at.desc())
        .options(selectinload(Deck.cards))
    )
    return list(result.scalars().all())


async def delete_deck(db: AsyncSession, deck_id: int, owner_id: int) -> bool:
    """Удаляет колоду. Возвращает True если удалена, False если не найдена / не владелец."""
    result = await db.execute(
        delete(Deck)
        .where(Deck.id == deck_id, Deck.owner_id == owner_id)
        .returning(Deck.id)
    )
    return result.scalar_one_or_none() is not None
