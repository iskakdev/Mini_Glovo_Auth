from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from database.models import RoleChoices


class UserProfileInputSchema(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: Optional[EmailStr]
    password: str
    age: Optional[int]
    phone_number: Optional[str]
    user_role: RoleChoices


class UserProfileOutSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: Optional[EmailStr]
    age: Optional[int]
    phone_number: Optional[str]
    user_role: RoleChoices


class UserLoginSchema(BaseModel):
    username: str
    password: str


class CurrentUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    user_role: RoleChoices
