from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostResponse, UserResponse, UserCreate, UserUpdate

router = APIRouter()
@router.post(
    '',
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException (
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        ) 
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException (
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    new_user = models.User(
        username=user.username,
        email=user.email
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user



@router.get('/{user_id}', response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).options(selectinload(models.User.posts)).where(models.User.id == user_id))
    found_user = result.scalars().first()
    if found_user:
        return found_user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details='User not found.')

@router.get('/{user_id}/posts', response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.posts))
        .where(models.User.id == user_id)
        .order_by(models.Post.date_posted.desc())
    )
    found_user = result.scalars().first()
    if found_user:
        return found_user.posts
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')


@router.put('/{user_id}', response_model=UserResponse)
async def update_user_full(user_id: int, update_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.username = update_data.username
    user.email = update_data.email
    await db.commit()
    await db.refresh(user)
    return user

@router.patch('/{user_id}', response_model=UserResponse)
async def user_update_partial(user_id: int, update_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    data_dict = update_data.model_dump(exclude_unset=True)
    for field, value in data_dict.items():
        if getattr(user, field) != value and field != 'image_file':
            check = await db.execute(
                select(models.User)
                .where(getattr(models.User, field) == value)
            )
            if check.scalars().first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field} already exists!")
    for field, value in data_dict.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user

@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()

