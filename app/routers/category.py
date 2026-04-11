from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import AuthDep
from fastapi import status

category_router = APIRouter(tags=["Category Management"])


@category_router.post('/category', response_model=CategoryResponse)
def create_category(db: SessionDep, user: AuthDep, category_data: CategoryCreate):
    category = Category(text=category_data.text, user_id=user.id)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating the category",
        )


@category_router.post('/todo/{todo_id}/category/{cat_id}', response_model=TodoResponse)
def add_category_to_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    already_linked = db.exec(
        select(TodoCategory).where(TodoCategory.todo_id == todo_id, TodoCategory.category_id == cat_id)
    ).one_or_none()
    if already_linked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already assigned to this todo")

    try:
        db.add(TodoCategory(todo_id=todo_id, category_id=cat_id))
        db.commit()
        db.refresh(todo)
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while assigning the category",
        )


@category_router.delete('/todo/{todo_id}/category/{cat_id}', status_code=status.HTTP_200_OK)
def remove_category_from_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    link = db.exec(
        select(TodoCategory).where(TodoCategory.todo_id == todo_id, TodoCategory.category_id == cat_id)
    ).one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category is not assigned to this todo")

    try:
        db.delete(link)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while removing the category",
        )


@category_router.get('/category/{cat_id}/todos', response_model=list[TodoResponse])
def get_todos_for_category(cat_id: int, db: SessionDep, user: AuthDep):
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return category.todos