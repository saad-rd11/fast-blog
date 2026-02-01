from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler
)
from routers import posts, users
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import Base, engine, get_db

# Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.mount('/media', StaticFiles(directory='media'), name='media')

templates = Jinja2Templates(directory='templates')

app.include_router(users.router, prefix='/api/users', tags=['users'])
app.include_router(posts.router, prefix='/api/posts', tags=['posts'])

@app.get('/post', include_in_schema=False, name='root')
@app.get("/", include_in_schema=False, name='home')
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    results = await db.execute(select(models.Post).options(selectinload(models.Post.author)).order_by(models.Post.date_posted.desc())
)
    
    posts = results.scalars().all() 
    
    return templates.TemplateResponse(
        request, 
        'home.html', 
        {"request": request, "posts": posts, "title": 'saad'}
    )



@app.get('/posts/{post_id}', name='post-for')
async def get_post(post_id: int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post was not found")
    return templates.TemplateResponse(request, 'post.html', {'post': post})





@app.get('/users/{user_id}/posts', include_in_schema=False, name='user_posts')
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    results = await db.execute(
        select(models.User)
        .options(selectinload(models.User.posts))
        .where(models.User.id == user_id)
        .order_by(models.Post.date_posted.desc())

    )
    
    found_user = results.scalars().first()
    if found_user:
        return templates.TemplateResponse(request, 'user_post.html', {"posts": found_user.posts,"user": found_user})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")



@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail if exception.detail else "Some error occurred!"
    )
    if request.url.path.startswith('/api'):
        return await http_exception_handler(
            request,
            exception
        )
    return templates.TemplateResponse(
        request,
        'error.html',
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message
        },
        status_code=exception.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith('/api'):
        return await request_validation_exception_handler(
            request,
            exception
        )
    return templates.TemplateResponse(
        request, 
        'error.html',
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid Request, plz check your input"
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )