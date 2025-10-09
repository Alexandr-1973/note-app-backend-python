from typing import List, Optional, Tuple

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


async def get_note(note_id: int, user: User, db: Session) -> Note:
    return db.query(Note).filter(and_(Note.id == note_id, Note.user_id == user.id)).first()


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


async def remove_note(note_id: int, user: User, db: AsyncSession) -> Note | None:

    stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == user.id))
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()

    if note:
        await db.delete(note)
        await db.commit()
        return note

    return None




# async def update_note(note_id: int, body: NoteUpdate, user: User, db: Session) -> Note | None:
#     note = db.query(Note).filter(and_(Note.id == note_id, Note.user_id == user.id)).first()
#     if note:
#         tags = db.query(Tag).filter(and_(Tag.id.in_(body.tags), Note.user_id == user.id)).all()
#         note.title = body.title
#         note.description = body.description
#         note.done = body.done
#         note.tags = tags
#         db.commit()
#     return note


# async def update_status_note(note_id: int, body: NoteStatusUpdate, user: User, db: Session) -> Note | None:
#     note = db.query(Note).filter(and_(Note.id == note_id, Note.user_id == user.id)).first()
#     if note:
#         note.done = body.done
#         db.commit()
#     return note




