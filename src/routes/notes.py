from typing import List, Optional
from sqlalchemy import func, or_, select, and_
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import Note
from src.schemas import NoteSchema, NoteResponseSchema, UserSchema, NotesPageSchema, NotePatchSchema
from src.repository import notes as repository_notes
from src.services.auth import auth_service, get_current_user

router = APIRouter(prefix='/notes', tags=["notes"])


@router.get("", response_model=NotesPageSchema)
async def read_notes(
    page: int = Query(1, ge=1),
    perPage: int = Query(12, ge=1, le=100),
    search: str = Query("", min_length=0),
    tag: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    tag_value = tag if tag not in (None, "", "All") else None
    notes, total_pages = await repository_notes.get_notes_page(
        db=db,
        user=current_user,
        page=page,
        per_page=perPage,
        search=search,
        tag=tag_value,
    )
    return {"notes": notes, "totalPages": total_pages}


@router.get("/{note_id}", response_model=NoteResponseSchema)
async def get_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    note = await repository_notes.get_note(note_id, current_user, db)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note

@router.patch("/{note_id}", response_model=NoteResponseSchema)
async def patch_note(
    note_id: int,
    body: NotePatchSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    update_data = body.model_dump(exclude_unset=True)
    note = await repository_notes.patch_note(
        note_id=note_id,
        user_id=current_user.id,
        db=db,
        update_data=update_data,
    )
    return note

@router.post(
    "",
    response_model=NoteResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    body: NoteSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):

    new_note = await repository_notes.create_note(body, current_user, db)
    return new_note


@router.delete("/{note_id}", response_model=NoteResponseSchema)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    deleted_note = await repository_notes.remove_note(note_id, current_user, db)
    if not deleted_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id={note_id} not found",
        )
    return deleted_note
