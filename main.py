import datetime

import hashlib
import pymorphy2
import requests
from flask import Flask, redirect, render_template, abort, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from PIL import Image
import os

from api import api_file
from data.recipes import Recipes

from data.users import User

from data import db_session
from forms.add_form import AddForm
from forms.registration_form import RegistrationForm

app = Flask(__name__)
app.register_blueprint(api_file.blueprint)
app.config['SECRET_KEY'] = 'fjowihuIJUhfiwofjioFOPJFfjsduhiIFIJIOWEJFJIWOkwvkwlkjJLKWJWEOPWadvkNBKHJHJjkHFHIJEOPQQUY41'
app.config['UPLOAD_FOLDER'] = 'static/images'
login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init('db/users.sqlite')
db_sess = db_session.create_session()


def resize_image(image):
    return image.resize((300, 200))


# Генерация токена пользователя для безопасности и приватности при использовании API
def generate_token(user_data):
    email, username = user_data
    value = str(email) + str(username)
    salt = ['fwv', 'ergpko3', 'jiwowdiojcnv']
    hashed_value = value.encode()
    for s in salt:
        for _ in range(20):
            hashed_value = hashlib.sha256(hashed_value + s.encode()).digest()
    return hashed_value


# Проверка является ли строка неанглийской
def noteng(data):
    for symb in data:
        if symb not in 'abcdefghijklmnopqrstuvwxyz' and not symb.isdigit():
            return True
    return False


# Проверка пароля на безопасность
def is_password_secure(password):
    is_dg = False
    is_lw = False
    is_up = False
    is_en = True
    if len(password) < 8:
        return 'short'
    for symb in password:
        if symb.isalpha() and noteng(symb.lower()):
            is_en = False
        if symb.isdigit():
            is_dg = True
        if symb.islower():
            is_lw = True
        if symb.isupper():
            is_up = True
    if not is_en:
        return 'noteng'
    elif is_dg and is_lw and is_up:
        return 'safe'
    else:
        return 'unsafe'


# Генерация зашифрованного пароля
def generate_hashed_password(default_password):
    salt = ['rvemkc', 'KJIHuhd78', 'pfkjwhuiUIWH', 'pFJIEWommwkcj', 'KOFJWIEomkFJWEOI']
    hashed_password = default_password.encode()
    for s in salt:
        for _ in range(50):
            hashed_password = hashlib.sha256(hashed_password + s.encode()).digest()
    return hashed_password


def main():
    app.run(port=8080, host='127.0.0.1')


# Перевод каждого ингредиента в нормальную форму слова для обеспечения удобного поиска
def ingredients_to_normal_form_function(ingredients):
    ingredients = ingredients.split(', ')
    ingredients_in_normal_form = []
    for x in ingredients:
        morph = pymorphy2.MorphAnalyzer()
        word_change = morph.parse(x.lower())
        added = False
        for y in word_change:
            if 'Abbr' in y.tag:
                ingredients_in_normal_form.append(y.word)
                added = True
                break
            elif 'Fixd' in y.tag:
                ingredients_in_normal_form.append(y.word)
                added = True
                break
            elif 'Pltm' in y.tag:
                ingredients_in_normal_form.append(y.inflect({'plur', 'nomn'}).word)
                added = True
                break
        if not added:
            ingredients_in_normal_form.append(word_change[0].normal_form)
    return ', '.join(sorted(ingredients_in_normal_form))


@login_manager.user_loader
def load_user(user_id):
    return db_sess.get(User, user_id)


@app.route('/')
def start_page():
    return render_template('base.html', current_user=current_user, title='Главная страница')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and check_password(user, generate_hashed_password(form.password.data).hex()):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_email_exists_check = db_sess.query(User).filter(User.email == form.email.data).first()
        user_username_exists_check = db_sess.query(User).filter(User.username == form.username.data).first()
        if user_email_exists_check is None and user_username_exists_check is None:
            # Проверка имени пользователя на длину
            if len(form.username.data) > 25:
                form.username.errors.append('Имя пользователя слишком длинное. Его длина должна быть не больше 25')
            # Проверка имени пользователя на содержание других букв кроме букв из английского алфавита и цифр
            elif noteng(form.username.data):
                form.username.errors.append('Имя пользователя должно состоять из букв латинского алфавита')
            # Проверка пароля на безопасность
            elif is_password_secure(form.password.data) == 'unsafe':
                form.password.errors.append('Пароль небезопасен. Используйте строчные и прописные буквы, а также цифры')
            # Проверка пароля на длину
            elif is_password_secure(form.password.data) == 'short':
                form.password.errors.append('Пароль должен быть длиной от 8 символов')
            # Проверка пароля на содержание других букв кроме букв из английского алфавита и цифр
            elif is_password_secure(form.password.data) == 'noteng':
                form.password.errors.append('Пароль должен состоять из букв английского алфавита и цифр')
            # Проверка равен ли повтор пароля оригинальному паролю
            elif form.password.data == form.password_repeat.data:
                user = User()
                user.created_date = datetime.datetime.now()
                user.username = form.username.data
                user.email = form.email.data
                user.hashed_password = generate_hashed_password(form.password.data).hex()
                user.hashed_token = generate_token([form.email.data, form.username.data]).hex()
                db_sess.add(user)
                db_sess.commit()
                user = db_sess.query(User).filter(User.email == form.email.data).first()
                login_user(user, remember=False)
                return redirect('/')
            else:
                return render_template('register.html', message='Пароли не совпадают', form=form)
        elif user_email_exists_check:
            form.email.errors.append('Пользователь с такой почтой уже существует')
        elif user_username_exists_check:
            form.username.errors.append('Пользователь с таким именем уже существует')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/my_recipes', methods=['GET'])
@app.route('/my_recipes/', methods=['GET'])
def my_recipes_show():
    # Функция показа рецептов пользователя. Остальной код в api_file.py
    if current_user.is_authenticated:
        recipes = requests.get('http://127.0.0.1:8080/api/get_recipes_of_one_user',
                               params={'user_token': db_sess.query(User).filter(
                                   User.id == current_user.id).first().hashed_token})
        if recipes.status_code == 200:
            json_recipes = recipes.json()
            return render_template('my_recipes.html', title='Мои рецепты', json_recipes=json_recipes['recipes'])
        else:
            abort(recipes.status_code)
    else:
        abort(401)


@app.route('/my_recipes/add', methods=['GET', 'POST'])
@app.route('/my_recipes/add/', methods=['GET', 'POST'])
def add_recipes_show():
    # Функция показа формы добавления рецептов
    if current_user.is_authenticated:
        form = AddForm()
        if form.validate_on_submit():
            # Проверка является ли поле времени приготовления числом.
            # (Дополнительная проверка требуется для предотвращения ошибки)
            try:
                if form.cooking_time.data // 10:
                    pass
            except TypeError:
                form.cooking_time.errors.append('Значение поля должно быть числом')
            photo = form.photo.data
            # В приложении стандартом изображений является формат png
            if not os.path.splitext(secure_filename(photo.filename))[1] == '.png':
                form.photo.errors.append('Изображение должно быть в формате png')
            else:
                time = datetime.datetime.now()
                title = form.title.data.lower()
                ingredients = form.ingredients.data
                description_of_cooking = form.description_of_cooking.data
                cooking_time = form.cooking_time.data
                is_private = form.is_private.data
                recipe = Recipes()
                recipe.created_date = time
                recipe.str_created_date = time.strftime('%d %b %Y')
                recipe.title = title
                recipe.ingredients = ingredients
                recipe.ingredients_in_normal_form = ingredients_to_normal_form_function(ingredients)
                recipe.description_of_cooking = description_of_cooking
                recipe.cooking_time = cooking_time
                recipe.is_private = is_private
                recipe.user_id = current_user.id
                db_sess.add(recipe)
                db_sess.commit()
                recipe_id = db_sess.query(Recipes).filter(Recipes.title == title).first().id
                try:
                    img = Image.open(photo)
                    resized_img = resize_image(img)
                    filename = secure_filename(photo.filename)
                    _, ext = os.path.splitext(filename)  # Получаем расширение файла
                    new_filename = f"{recipe_id}{ext}"
                    resized_img.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    return redirect('/my_recipes')
                except Exception:
                    db_sess.delete(recipe)
                    db_sess.commit()
                    form.photo.errors.append('Можно загружать только изображения в формате png')
        return render_template('add_form.html', title='Добавление рецептов', form=form)
    else:
        abort(401)


@app.route('/recipes/del/id/<int:recipe_id>', methods=['GET', 'DELETE'])
@app.route('/recipes/del/id/<int:recipe_id>/', methods=['GET', 'DELETE'])
def delete_recipe_from_db(recipe_id):
    # Удаление рецепта из базы данных с помощью кнопки "Удалить". Остальной код в api_file.py
    if current_user.is_authenticated:
        requests.delete(f'http://127.0.0.1:8080/api/del/id/{recipe_id}',
                        params={'user_token': db_sess.query(User).filter(
                            User.id == current_user.id).first().hashed_token})
        return redirect('/my_recipes')
    else:
        abort(403)


@app.route('/recipes/get/id/<int:recipe_id>', methods=['GET', 'DELETE'])
@app.route('/recipes/get/id/<int:recipe_id>/', methods=['GET', 'DELETE'])
def details_of_recipe(recipe_id):
    # Получение подробной информации о рецепте с помощью кнопки "Подробнее". Остальной код в api_file.py
    if current_user.is_authenticated:
        recipes = requests.get(f'http://127.0.0.1:8080/api/get/id/{recipe_id}',
                               params={'user_token': db_sess.query(User).filter(
                                   User.id == current_user.id).first().hashed_token})
        if recipes.status_code == 200:
            json_recipe = recipes.json()
            if int(json_recipe['recipe'][0]['user_id']) == int(current_user.id):
                return render_template('recipe_card.html', title='Мои рецепты', json_recipe=json_recipe['recipe'],
                                       message='Это ваш рецепт.')
            else:
                return render_template(
                    'recipe_card.html', title='Мои рецепты',
                    json_recipe=json_recipe['recipe'],
                    message=f'Рецепт пользователя @',
                    author=db_sess.get(User, int(json_recipe["recipe"][0]["user_id"])).username)
        else:
            abort(recipes.status_code)
    else:
        abort(403)


def check_password(user, password):
    # Проверка совпадает ли имя введённого пользователя с паролем этого пользователя в базе данных
    if user is None or password is None:
        return False
    user_request = db_sess.query(User).filter(User.username == user.username).first()
    if password == user_request.hashed_password:
        return True
    return False


@app.route('/search')
@app.route('/search/')
def search():
    # Функция поиска с использованием различных параметров в базе данных. Остальной код в api_file.py
    if current_user.is_authenticated:
        query = request.args.get('query')
        search_type = request.args.get('searchType')
        recipes = requests.get(f'http://127.0.0.1:8080/api/get_search_results',
                               params={'user_token': db_sess.query(User).filter(
                                   User.id == current_user.id).first().hashed_token, 'query': query,
                                       'search_type': search_type})
        json_recipes = recipes.json()
        if len(json_recipes['recipes']) == 0:
            return render_template('search_results.html', title='Результаты поиска', is_found=False)
        return render_template('search_results.html', title='Результаты поиска', json_recipes=json_recipes['recipes'],
                               is_found=True)
    else:
        abort(403)


@app.route('/logout')
@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_page.html', message='Страница не найдена. (404)'), 404


@app.errorhandler(401)
def unauthorized_user(error):
    return render_template('error_page.html', message='Отказано в доступе. Пользователь не авторизован. (401)'), 401


@app.errorhandler(403)
def forbidden(error):
    return render_template('error_page.html', message='Доступ запрещён. (403)'), 403


if __name__ == '__main__':
    main()
