from typing import List
import time
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from app import sqlalchemy_models as sm
from app import pydantic_models as pm
from app import utility, database
from app.database import engine, get_db
from app.environment import CLIENT_HOSTNAME, CLIENT_PORT

app = FastAPI(title="Examplicious", docs_url='/')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://{CLIENT_HOSTNAME}:{CLIENT_PORT}",
        f"https://{CLIENT_HOSTNAME}:{CLIENT_PORT}",
        f"http://{CLIENT_HOSTNAME}:80",
        f"https://{CLIENT_HOSTNAME}:443",
        f"http://{CLIENT_HOSTNAME}",
        f"https://{CLIENT_HOSTNAME}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

########################################################################################################################
# Authentication

from fastapi import Depends, FastAPI, HTTPException, status
from app.authentication import verify_credentials, get_current_user, create_token, get_password_hash


@app.post("/sign-in", response_model=str)
def sign_in(data: pm.LoginForm):
    if verify_credentials(data.username, data.password):
        return create_token({"sub": data.username})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


########################################################################################################################
# Users

@app.get("/users", response_model=List[pm.User])
def get_users(db=Depends(get_db)):
    users = db.query(sm.User).all()
    return users


@app.get("/users/me", response_model=pm.User)
def get_user(db=Depends(get_db),
             current_user: pm.User = Depends(get_current_user)):
    user = db.query(sm.User).filter_by(username=current_user.username).one()
    return user


@app.post("/users", response_model=pm.User)
def post_user(item: pm.UserCreate,
              db=Depends(get_db),
              ):
    item_dict = item.dict()
    item_dict['hashed_password'] = get_password_hash(item.password)
    item_dict.pop('password')

    print(item)
    print(item_dict)
    all_users = db.query(sm.User)
    if all_users.filter_by(username=item.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is taken")
    if all_users.filter_by(email=item.email).filter(sm.User.email.isnot(None)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is taken")

    db_user = sm.User(**item_dict)
    db.add(db_user)
    db.commit()

    return db_user


########################################################################################################################
# Articles

@app.get("/articles", response_model=List[pm.Article])
def get_article(db=Depends(get_db)):
    articles = db.query(sm.Article) \
        .order_by(sm.Article.id.desc()) \
        .all()
    return articles


@app.post("/articles", response_model=pm.Article)
def post_article(item: pm.ArticleCreate,
                 db=Depends(get_db),
                 current_user: pm.User = Depends(get_current_user)):
    db_article = sm.Article(**item.dict())
    db.add(db_article)
    db.commit()

    return db_article


########################################################################################################################
# Custom HTTP Responses
from pydantic import BaseModel, EmailStr
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.exceptions import RequestValidationError, ValidationError
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler


# Make validation error HTTP responses more readable
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=418,
        content={"detail": str(exc)},
    )


########################################################################################################################
# Admin functions

@app.get("/fill_db")
def get_article(password: str = None):
    if password == "babymonkey":
        utility.add_mock_data()
        return PlainTextResponse("fill_db success")
    return PlainTextResponse("Wrong password")


@app.get("/reset_db")
def get_article(password: str = None):
    if password == "babymonkey":
        database.delete_all_tables()
        database.initialize_db()
        return PlainTextResponse("reset_db success")
    return PlainTextResponse("Wrong password")
