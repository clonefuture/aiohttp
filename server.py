import asyncio
import sys

from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, DateTime, func, Text, ForeignKey
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError
import json
import bcrypt
from typing import Optional

app = web.Application()

PG_DSN = 'postgresql+asyncpg://app:1234@127.0.0.1:5431/app'
engine = create_async_engine(PG_DSN)
Base = declarative_base()


class HttpError(web.HTTPException):
    def __init__(self, message, *args, **kwargs):
        json_response = json.dumps({
            'status': 'error',
            'message': message
        })
        
        super().__init__(*args, **kwargs, text=json_response, content_type='application/json')


class BadRequest(HttpError):
    status_code = 400


class NotFound(HttpError):
    status_code = 404


class CreateUserSchema(BaseModel):
    username: str
    password: str


class PatchUserSchema(BaseModel):
    username: Optional[str]
    password: Optional[str]


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, )
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String, nullable=False)
    registration_time = Column(DateTime, server_default=func.now())
    adverts = relationship('Advert', backref='author')


class Advert(Base):
    __tablename__ = 'adverts'

    id = Column(Integer, primary_key=True)
    topic = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    create_date = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))


async def init_orm(app):
    print('START')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
        async_session_maker = sessionmaker(engine, expire_on_commit=False,
                                           class_=AsyncSession)
        app.async_session_maker = async_session_maker
        yield
    print('SHUT DOWN')


async def get_user(user_id, session):
    user = await session.get(Users, user_id)
    if not user:
        raise NotFound(message='user not found')
    return user


class UserView(web.View):

    async def get(self):
        user_id = int(self.request.match_info['user_id'])
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            return web.json_response({
                'username': user.username,
                'registration_time': int(user.registration_time.timestamp())
            })

    async def post(self):
        json_data = await self.request.json()
        try:
            json_data_validated = CreateUserSchema(**json_data).dict()
        except ValidationError as err:
            raise BadRequest(message=err.errors())
        json_data_validated['password'] = (bcrypt.hashpw(
            json_data_validated['password'].encode(),
            salt=bcrypt.gensalt())).decode()
        new_user = Users(**json_data_validated)
        async with app.async_session_maker() as session:
            try:
                session.add(new_user)
                await session.commit()
            except IntegrityError:
                raise BadRequest(message='user already exists')
            return web.json_response({'id': new_user.id})

    async def patch(self):
        user_id = int(self.request.match_info['user_id'])
        user_data = await self.request.json()
        user_data_validated = PatchUserSchema(**user_data).dict(exclude_none=True)
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            for key, value in user_data_validated.items():
                setattr(user, key, value)
            session.add(user)
            await session.commit()
            return web.json_response({'status': 'success'})

    async def delete(self):
        user_id = int(self.request.match_info['user_id'])
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            await session.delete(user)
            await session.commit()
            return web.json_response({'status': 'success'})


app.add_routes([web.post('/users', UserView),
                web.get('/users/{user_id:\d+}', UserView),
                web.patch('/users/{user_id:\d+}', UserView),
                web.delete('/users/{user_id:\d+}', UserView)
                ]
               )

app.cleanup_ctx.append(init_orm)


web.run_app(app, host='127.0.0.1', port=8080)
