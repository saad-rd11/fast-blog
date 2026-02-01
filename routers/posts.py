from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate

router = APIRouter()

@router.post(
    '',
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(post.user_id == models.User.id)
    )
    found_user = result.scalars().first()
    if found_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    new_post = models.Post(
        title=post.title,
        content=post.content,
        author=found_user
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=['author'])
    return new_post


@router.delete('/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post was not found")


    await db.delete(post)
    await db.commit()


@router.patch('/{post_id}', response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: PostUpdate, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post was not found")

    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    await db.commit()
    await db.refresh(post, attribute_names=['author']) 

    return post



@router.put('/{post_id}', response_model=PostResponse)
async def update_post_full(post_id: int, post_data: PostCreate, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post was not found")
    
    if post_data.user_id != post.user_id:
        result = db.execute(
            select(models.User)
            .where(models.User.id == post_data.user_id)
        )
        if not (result.scalars().first()):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id
    await db.commit()
    await db.refresh(post, attribute_names=['author']) 

    return post


@router.get('', response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
    )
    posts = results.scalars().all()
    return posts