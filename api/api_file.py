import os

import flask
import pymorphy2
from flask import jsonify, request, abort, render_template

from data import db_session
from data.users import User
from data.recipes import Recipes

blueprint = flask.Blueprint(
    'api_file',
    __name__,
    template_folder='templates'
)


def ingredients_to_normal_form_function(ingredients):
    if ingredients is not None:
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
    return ''


@blueprint.route('/api/get_recipes_of_one_user', methods=['GET'])
@blueprint.route('/api/get_recipes_of_one_user/', methods=['GET'])
def get_recipes_of_one_user():
    # Функция получения всех рецептов пользователя, а затем возвращение этих рецептов функции my_recipes_show в main.py
    user_token = request.args.get('user_token')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.hashed_token == user_token).first()
    if user:
        recipes_of_user = db_sess.query(Recipes).filter(Recipes.user_id == int(user.id))
        return jsonify({
            'recipes':
                [item.to_dict(only=(
                    'id', 'title', 'ingredients', 'ingredients_in_normal_form', 'description_of_cooking',
                    'cooking_time',
                    'created_date', 'is_private', 'user_id', 'str_created_date')) for item in recipes_of_user]
        })
    else:
        abort(403)


@blueprint.route('/api/del/id/<int:recipe_id>', methods=['GET', 'DELETE'])
@blueprint.route('/api/del/id/<int:recipe_id>/', methods=['GET', 'DELETE'])
def delete_recipe(recipe_id):
    # Функция удаления определённого рецепта определённого пользователя при помощи кнопки "Удалить". Эту функцию
    # вызывает функция delete_recipe_from_db из main.py
    user_token = request.args.get('user_token')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.hashed_token == user_token).first()
    if user:
        recipe = db_sess.get(Recipes, recipe_id)
        if not recipe:
            abort(404)
        if recipe.user_id != int(user.id):
            abort(403)
        db_sess.delete(recipe)
        db_sess.commit()
        photo_path = f'static/images/{recipe_id}.png'
        if os.path.exists(photo_path):
            os.remove(photo_path)
            return jsonify({'success': 'ok'})
    else:
        abort(403)


@blueprint.route('/api/get/id/<int:recipe_id>', methods=['GET', 'DELETE'])
@blueprint.route('/api/get/id/<int:recipe_id>/', methods=['GET', 'DELETE'])
def get_recipe(recipe_id):
    # Функция получения определённого рецепта определённого пользователя. Эту функцию вызывает функция details_of_recipe
    # из main.py. Возвращает json файл с данными о рецепте
    user_token = request.args.get('user_token')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.hashed_token == user_token).first()
    if user:
        recipe = db_sess.get(Recipes, recipe_id)
        if not recipe:
            abort(404)
        if recipe.user_id != int(user.id) and recipe.is_private:
            abort(403)
        return jsonify({
            'recipe':
                [recipe.to_dict(only=(
                    'id', 'title', 'ingredients', 'ingredients_in_normal_form', 'description_of_cooking',
                    'cooking_time',
                    'created_date', 'is_private', 'user_id', 'str_created_date'))]
        })
    else:
        abort(403)


@blueprint.route('/api/get_search_results')
@blueprint.route('/api/get_search_results/')
def get_search_results():
    # Функция получения результатов поиска. Эту функцию вызывает функция search из файла main.py. Возвращает все рецепты
    # на основании запроса в поисковой строке.
    user_token = request.args.get('user_token')
    query = request.args.get('query')
    search_type = request.args.get('search_type')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.hashed_token == user_token).first()
    if user:
        if search_type == 'title':
            recipes = []
            if query is None:
                query = ''
            recipes_public = db_sess.query(Recipes).filter(
                Recipes.title.like(f'%{query.lower()}%'),
                Recipes.is_private != 1)
            recipes_private = db_sess.query(Recipes).filter(Recipes.user_id == user.id, Recipes.is_private == 1,
                                                            Recipes.title.like(f'%{query.lower()}%'))
            for recipe in recipes_public:
                recipes.append(recipe)
            for recipe in recipes_private:
                recipes.append(recipe)
            return jsonify({
                'recipes':
                    [item.to_dict(only=(
                        'id', 'title', 'ingredients', 'ingredients_in_normal_form', 'description_of_cooking',
                        'cooking_time',
                        'created_date', 'is_private', 'user_id', 'str_created_date')) for item in recipes]
            })
        else:
            recipes = []
            ingredients = ingredients_to_normal_form_function(query)
            ingredients = '%'.join(ingredients.split(', '))
            recipes_public = db_sess.query(Recipes).filter(Recipes.ingredients_in_normal_form.like(f'%{ingredients}%'),
                                                           Recipes.is_private != 1)
            recipes_private = db_sess.query(Recipes).filter(Recipes.user_id == user.id, Recipes.is_private == 1,
                                                            Recipes.ingredients_in_normal_form.like(f'%{ingredients}%'))
            for recipe in recipes_public:
                recipes.append(recipe)
            for recipe in recipes_private:
                recipes.append(recipe)
            return jsonify({
                'recipes':
                    [item.to_dict(only=(
                        'id', 'title', 'ingredients', 'ingredients_in_normal_form', 'description_of_cooking',
                        'cooking_time',
                        'created_date', 'is_private', 'user_id', 'str_created_date')) for item in recipes]
            })
    else:
        abort(403)


@blueprint.errorhandler(403)
def forbidden(error):
    return render_template('error_page.html', message='Доступ запрещён. (403)'), 403
