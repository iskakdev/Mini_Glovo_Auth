from fastapi import APIRouter, Depends, HTTPException, Body
from database.db import SessionLocal
from database.models import UserProfile, RefreshToken
from database.schema import UserProfileInputSchema, UserProfileOutSchema, UserLoginSchema, CurrentUserSchema
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from config import (SECRET_KEY, ALGORITHM,
                     ACCESS_TOKEN_LIFETIME,
                     REFRESH_TOKEN_LIFETIME)
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from typing import Optional


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_schema = OAuth2PasswordBearer(tokenUrl='auth/login/')

auth_router = APIRouter(prefix='/auth', tags=['Auth'])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


credentials_exception = HTTPException(
    status_code=401,
    detail='Access token неправильный либо срок истек',
    headers={'WWW-Authenticate': 'Bearer'}
)


def get_current_user(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get('sub')

        if subject is None:
            raise credentials_exception

        user_id = int(subject)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user_db = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    if not user_db:
        raise credentials_exception

    return user_db


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_LIFETIME)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    return create_access_token(data, expires_delta=timedelta(days=REFRESH_TOKEN_LIFETIME))


def get_token_data(user: UserProfile):
    return {'sub': str(user.id), 'username': user.username, 'status': user.user_role.value}


@auth_router.post('/register/', response_model=dict)
async def register(user: UserProfileInputSchema, db: Session = Depends(get_db)):
    user_db = db.query(UserProfile).filter(UserProfile.username == user.username).first()
    email_db = db.query(UserProfile).filter(UserProfile.email == user.email).first()
    if user_db:
        raise HTTPException(detail='Такой ник уже есть', status_code=400)
    elif email_db:
        raise HTTPException(detail='Такая почта уже есть', status_code=400)

    hash_password = get_password_hash(user.password)
    user_data = UserProfile(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        age=user.age,
        phone_number=user.phone_number,
        password=hash_password,
        user_role=user.user_role
    )
    db.add(user_data)
    db.commit()
    db.refresh(user_data)
    return {'message': 'Вы успешно зарегистрировались'}


@auth_router.post('/login/', response_model=dict)
async def login(user: UserLoginSchema, db: Session = Depends(get_db)):
    user_db = db.query(UserProfile).filter(UserProfile.username == user.username).first()
    if not user_db or not verify_password(user.password, user_db.password):
        raise HTTPException(detail='Данные которые вы ввели, неправильные', status_code=401)

    token_data = get_token_data(user_db)

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    token_db = RefreshToken(user_id=user_db.id, token=refresh_token)
    db.add(token_db)
    db.commit()

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'Bearer'}


@auth_router.post('/logout/', response_model=dict)
async def logout(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    stored_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

    if not stored_token:
        raise HTTPException(status_code=401, detail='Данные неправильные')

    db.delete(stored_token)
    db.commit()

    return {'message': 'Вы вышли'}


@auth_router.post('/refresh')
async def refresh(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    stored_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

    if not stored_token:
        raise HTTPException(status_code=401, detail='Данные неправильные')

    try:
        jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        db.delete(stored_token)
        db.commit()
        raise HTTPException(status_code=401, detail='Refresh token истёк либо недействителен')

    user_db = stored_token.token_user
    token_data = get_token_data(user_db)

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    db.delete(stored_token)
    token_db = RefreshToken(user_id=user_db.id, token=new_refresh_token)
    db.add(token_db)
    db.commit()

    return {'access_token': new_access_token, 'refresh_token': new_refresh_token, 'token_type': 'Bearer'}


@auth_router.get('/verify', response_model=CurrentUserSchema)
async def verify_access_token(current_user: UserProfile = Depends(get_current_user)):
    return current_user


@auth_router.get('/me', response_model=UserProfileOutSchema)
async def user_me(profile: UserProfile = Depends(get_current_user)):
    return profile