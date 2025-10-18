from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.database.models import Note, User
from src.schemas import NoteSchema, NoteResponseSchema

async def get_notes_page(
    db: AsyncSession,
    user: User,
    page: int,
    per_page: int,
    search: str = "",
    tag: Optional[str] = None,
) -> Tuple[List[Note], int]:

    base_filters = [Note.user_id == user.id]

    if tag:
        base_filters.append(Note.tag == tag)

    if search:
        like = f"%{search}%"
        base_filters.append(
            or_(Note.title.ilike(like), Note.content.ilike(like))
        )

    count_stmt = select(func.count()).select_from(Note).where(*base_filters)
    total: int = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * per_page

    data_stmt = (
        select(Note)
        .where(*base_filters)
        .order_by(Note.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(data_stmt)
    notes = result.scalars().all()

    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
    return notes, total_pages


async def get_note(note_id: int, user: User, db: AsyncSession) -> Note | None:
    stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == user.id))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_note(body: NoteSchema, user: User, db: AsyncSession) -> Note:
    new_note = Note(
        title=body.title,
        content=body.content,
        tag=body.tag,
        user_id=user.id,
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note

async def patch_note(
    note_id: int,
    user_id: int,
    db: AsyncSession,
    update_data: dict,
) -> Note:

    print(update_data)
    print (note_id, user_id)
    result = await db.execute(
        select(Note).where(and_(Note.id == note_id, Note.user_id == user_id))
    )
    note = result.scalar_one_or_none()
    print (note.title)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if not update_data:
        return note

    for key, value in update_data.items():
        setattr(note, key, value)

    await db.commit()
    await db.refresh(note)
    return note


async def remove_note(note_id: int, user: User, db: AsyncSession) -> Note | None:

    stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == user.id))
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()

    if note:
        await db.delete(note)
        await db.commit()
        return note

    return None

