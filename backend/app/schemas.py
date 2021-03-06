"""
Define Pydantic models to validate request/response shapes.
We call these schemas to avoid confusion with SQLAlchemy models.
"""
from pydantic import BaseModel, EmailStr


##############################
# Authentication

class LoginCredentials(BaseModel):
    username: str
    password: str


##############################
# User

class UserBase(BaseModel):
    username: str
    email: EmailStr = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class UserInDB(UserBase):
    hashed_password: str


##############################
# Post

class PostBase(BaseModel):
    title: str
    body: str


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int

    class Config:
        orm_mode = True
