import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

    # Use the after_request decorator to set Access-Control-Allow
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # categories endpoint to handle GET requests
    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.type).all()

        if len(categories) == 0:
            abort(404)

        return jsonify({'success': True, 'categories': {
                       category.id: category.type for category in categories}})

    # endpoint to handle GET requests for questions, including pagination
    # (every 10 questions).
    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.order_by(Category.type).all()

        if len(current_questions) == 0 or current_questions is None:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': {category.id: category.type for category in categories},
            'current_category': None
        })

    # Create an endpoint to DELETE question using a question ID.
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except BaseException:
            abort(422)

    # endpoint to POST a new question to the list
    @app.route('/questions', methods=['POST'])
    def post_question():
        body = request.get_json()

        if body.get('question') == '' or body.get('answer') == '':
            abort(422)

        else:
            new_question = body.get('question')
            new_answer = body.get('answer')
            new_category = body.get('category')
            new_difficulty = body.get('difficulty')
        print(body)
        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty
            )

            question.insert()
            return jsonify({
                'success': True,
                'created': question.id
            })
        except BaseException:
            abort(422)

    # POST endpoint to get questions based on a search term.
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_term = body.get('searchTerm')

        if search_term:
            search_results = Question.query.filter(
                Question.question.ilike(
                    '%{}%'.format(search_term))).all()
            current_questions = paginate_questions(request, search_results)

            if search_results == []:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(current_questions),
                'current_category': None
            })

        else:
            abort(404)

    # GET endpoint to get questions based on category.

    @app.route('/categories/<int:category_id>/questions')
    def get_category_questions(category_id):
        try:
            questions = Question.query.filter(
                Question.category == category_id).all()

            if questions == []:
                abort(404)

            return jsonify({
                'success': True,
                'questions': [question.format() for question in questions],
                'total_questions': len(questions),
                'current_category': category_id
            })
        except BaseException:
            abort(404)

    # POST endpoint to get questions to play the quiz.
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()
        previous = body.get('previous_questions', [])
        quiz_category = body.get('quiz_category', None)
        if 'quiz_category' not in body and 'previous' in body:
            abort(422)

        try:
            if quiz_category['id'] == 0:
                filter_questions = Question.query.filter(
                    Question.id.notin_(previous)).all()
            else:
                filter_questions = Question.query.filter(
                    Question.category == quiz_category['id']).filter(
                    Question.id.notin_(previous)).all()
            random_question = []

            if len(filter_questions) > 0:
                random_question = random.choice(filter_questions).format()
                return jsonify({
                    'success': True,
                    'question': random_question
                })
            else:
                return jsonify({
                    'success': False,
                    'question': None
                })

        except BaseException:
            abort(422)

    # error handlers for all expected errors
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Not Found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable'
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method is not allowed'
        }), 405
    return app
