from fastapi import APIRouter, Depends, HTTPException
from database.models import UserProfile
from database.schema import UserProfileInputSchema, UserProfileOutSchema
from database.db import SessionLocal
from typing import List
from sqlalchemy.orm import Session

user_services_router = APIRouter(prefix='/user_services', tags=['User Services'])

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@user_services_router.get('/', response_model=List[UserProfileOutSchema])
async def list_user(db: Session = Depends(get_db)):
    return db.query(UserProfile).all()


@user_services_router.get('/{user_id}/', response_model=UserProfileOutSchema)
async def detail_user(user_id: int, db: Session = Depends(get_db)):
    user_db = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user_db:
        raise HTTPException(detail='Таких данных нет', status_code=400)

    return user_db


@user_services_router.put('/{user_id}/', response_model=dict)
async def update_user(user_id: int, user: UserProfileInputSchema,
                         db: Session = Depends(get_db)):
    user_db = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user_db:
        raise HTTPException(detail='Таких данных нет', status_code=400)

    for user_key, user_value in user.dict().items():
        setattr(user_db, user_key, user_value)

    db.commit()
    db.refresh(user_db)
    return {'massage': 'Пользователь успешно изменен'}


@user_services_router.delete('/{user_id}/', response_model=dict)
async def delete_user(user_id: int, db:  Session = Depends(get_db)):
    user_db = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user_db:
        raise HTTPException(detail='Таких данных нет', status_code=400)

    db.delete(user_db)
    db.commit()
    return {'massage': 'Пользователь успешно удален'}
