import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    recipes_of_user = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    recipes = orm.relationship("Recipes", back_populates='user')
    hashed_token = sqlalchemy.Column(sqlalchemy.String, nullable=False)
