# -*- coding: utf-8 -*

from flask import Flask, render_template, request, json, send_from_directory, jsonify, Response
from flask_cors import CORS, cross_origin
from config import Config
import ControllerDB
from data import response_messages
import os, json

app = Flask(__name__)
# permit all origins:
CORS(app)

@app.route("/", methods = ["GET"])
def index(): return render_template("index.html")

@app.route("/new_game_<username>_topic_<topic>", methods = ["GET"])
def new_game(username, topic):
    try:
        user = ControllerDB.get_user_by_name(username)
        if user != None:
            message = response_messages.msgs.get('username_not_available')
            return json.dumps({ 'status': False, 'message': message }, ensure_ascii=False)
        # Add user in database:
        ControllerDB.insert_user(username)            
        # Create game object:
        new_game = create_new_game(username, topic)
        print("New game: " + str(new_game))
        # Add game object in database:
        ControllerDB.insert_new_game(new_game)
        # return response:
        message = response_messages.msgs.get('new_game_ok')
        # remove the property _id:
        del new_game["_id"]     
        # send response:
        return json.dumps({ 'status': True, 'message': message, 'game': new_game }, ensure_ascii= False)

    except Exception as e:
        print(e)
        print(e.args)
        return json.dumps({ "status": False, "message": "Error interno del servidor" }, ensure_ascii= False)
    pass


@app.route("/answer_question_id_game_<idgame>_answer_<answer>", methods = ["GET"])
def answer(idgame, answer):
    try:
        # find the game in the db:
        game = json.loads(ControllerDB.get_game_by_id(idgame))
        actual_round = int(game.get('current_round'))
        answer = str(answer)
        topic = game.get("topic_game")
        # get list of all questions in the db:
        questions = ControllerDB.get_all_questions_by_topic(topic)
        # filter:
        my_question = questions[actual_round - 1]
        print("Question: {}".format(my_question))
        # question = get_answers_by_topic(game.get("topic_game")).get("all_questions")[actual_round - 1]
        result = my_question.get("correct") == answer
        total_correct = game.get('total_correct')
        total_errors = game.get('total_errors')
        if result: total_correct += 1
        else: total_errors += 1        

        new_game = {
            'id_game': game.get('id_game'),
            'topic_game': game.get('topic_game'),
            'username': game.get('username'),
            'current_round': (game.get('current_round') + 1),
            'total_correct': total_correct,
            'total_errors': total_errors
        }
        print("nuevo objeto game:")
        print(new_game)
        # save the new game in db:
        ControllerDB.update_game(new_game)
        return json.dumps({ "status": True, "result": result, "game": new_game }, ensure_ascii= False)

    except Exception as e:
        print(e)
        print(e.args)
        return json.dumps({ "status": False, "message": "Error interno del servidor" }, ensure_ascii= False)

@app.route("/get_new_question_id_<idgame>", methods = ["GET"])
def get_new_question(idgame):
    try:
        # find the game in the db:
        my_game = json.loads(ControllerDB.get_game_by_id(int(idgame)))
        actual_round = int(my_game.get('current_round'))
        all_questions = ControllerDB.get_all_questions_by_topic(my_game.get("topic_game"))
        send_question = all_questions[actual_round - 1]

        json_data = {
            'status': True,
            'id_question': send_question.get("id_question"),
            'question': send_question.get("question"),
            'answers': send_question.get("answers")
        }
        return json_data
        
    except Exception as e:
        print(e)
        print(e.args)
        return json.dumps({ "status": False, "message": "Error interno del servidor" }, ensure_ascii= False)
    pass

# @app.route("/end_game_<username>", methods = ["GET"])
# def end_game(username):
#     try:
#         # remove user from the list
#         for index in range(0, len(users)):
#             if users[index].get('username') == username:
#                 users.pop(index)
#     except Exception as e:
#         pass

# return css and static files:
@app.route('/public/<path:path>')
def send_css_and_media(path):
    return send_from_directory('public', path)

@app.errorhandler(404)
def resource_not_found(error = None):
    return "404 not found: {}".format(request.url)
    # return render_template("404errorPage.html")

#################### LOGIC: ###############################

def create_new_game(username, topic):
    length_games = ControllerDB.get_length_games()
    print("LEN: {}".format(length_games))
    return {
        "id_game": (int(length_games) + 1),
        "topic_game": topic,
        "username": username,
        "current_round": 1,
        "total_correct": 0,
        "total_errors": 0
    }


def update_json_games(new_game_data):
    # Rewrite the JSON games.json:
    route = (os.environ["PP_ROUTE"] + "/trivia_game/data/games.json")
    with open(route,'r+') as json_file:
        data = json_file.read()
        json_file.seek(0)
        json_file.write(json.dumps(new_game_data))
        json_file.truncate()

def get_json_games():
    return json.loads(read_file_games_data())

def read_file_games_data():
    route = (os.environ["PP_ROUTE"] + "/trivia_game/data/games.json" )
    f = open(route, "r").read()
    return f

def read_file_trivia_data():
    route = (os.environ["PP_ROUTE"] + "/trivia_game/data/trivia_data.json" )
    f = open(route, "r").read()
    return f

def get_json_trivia_data():
    return json.loads(read_file_trivia_data())

def get_answers_by_topic(topic):
    data = get_json_trivia_data()
    for elem in data:
        if elem.get('topic') == topic:
            return elem

###### End Logic ########################

# RUN:
def test():
    app.run(debug=True)

def run():
    app.run(debug=False)

if __name__ == '__main__':
    if (Config.config.get("debug_mode")):
        test()
    else: 
        run()

