from database.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey
from typing import Optional, List
from enum import Enum as PyEnum
from datetime import datetime


class RoleChoices(PyEnum):
    simple_user = 'simple_user'
    courier = 'courier'
    store_owner = 'store_owner'


class UserProfile(Base):
    __tablename__ = 'mini_glovo_profile'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_role: Mapped[RoleChoices] = mapped_column(Enum(RoleChoices), default=RoleChoices.simple_user)

    user_token: Mapped[List['RefreshToken']] = relationship('RefreshToken',
                                                            back_populates='token_user',
                                                            cascade='all, delete-orphan')


class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('mini_glovo_profile.id'))
    token: Mapped[str] = mapped_column(String)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())

    token_user: Mapped[UserProfile] = relationship(UserProfile, back_populates='user_token')
