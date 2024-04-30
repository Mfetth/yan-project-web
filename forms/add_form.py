from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, IntegerField, FileField
from wtforms.validators import DataRequired


class AddForm(FlaskForm):
    title = StringField('Название блюда', validators=[DataRequired()])
    ingredients = StringField('Ингредиенты (через запятую)', validators=[DataRequired()])
    description_of_cooking = StringField('Описание приготовления', validators=[DataRequired()])
    cooking_time = IntegerField('Время приготовления (в минутах)', validators=[DataRequired()])
    photo = FileField('Изображение', validators=[DataRequired()])
    is_private = BooleanField('Сделать рецепт приватным?')
    submit = SubmitField('Создать рецепт', validators=[DataRequired()])
