import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Recipes(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'recipes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    ingredients = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    ingredients_in_normal_form = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description_of_cooking = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    cooking_time = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    str_created_date = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now())
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')
