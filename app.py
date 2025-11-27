# app.py
import os
import random
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

try:
    from src.interviewer import SciBoxHelper
    from src.level_system import UserLevelSystem
    from src.settings import CNT_QUESTION, CNT_CODES, THEME, API_KEY
except ImportError as e:
    print(f"Import error: {e}")
    print("Using demo mode...")
    
    # Fallback классы
    class SciBoxHelper:
        def generate_question(self, topic, difficulty_level):
            return f"Вопрос по теме {topic}: Объясните основные принципы."
        def evaluate_answer(self, question, answer):
            return 7, "Хороший ответ"
        def generate_feedback(self, question, answer, score):
            return "Хорошая работа!"
        def generate_coding_task(self, topic, difficulty_level):
            return f"Напишите функцию для работы с {topic}"
        def evaluate_code(self, task, code):
            return 15, "Код рабочий"
        def generate_code_feedback(self, task, code):
            return "Хороший стиль программирования"
    
    class UserLevelSystem:
        def __init__(self, cnt_questions, cnt_codes):
            self.user_lvl = 1
            self.total_score = 0
        def update_user_lvl(self, score):
            self.total_score += score
        def get_user_lvl(self):
            return "Junior"
    
    CNT_QUESTION = 3
    CNT_CODES = 2
    THEME = ['OOP', 'Algorithms']
    API_KEY = os.getenv('API_KEY', 'demo-key')

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Конфигурация для продакшена
if os.getenv('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
else:
    app.config['DEBUG'] = True

sci_box = SciBoxHelper(API_KEY)
user_system = UserLevelSystem(CNT_QUESTION, CNT_CODES)

interview_state = {
    'current_question_index': 0,
    'current_code_index': 0,
    'total_score': 0,
    'completed': False
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# API endpoints
@app.route('/api/start_interview', methods=['POST'])
def start_interview():
    global interview_state, user_system
    
    interview_state = {
        'current_question_index': 0,
        'current_code_index': 0,
        'total_score': 0,
        'completed': False
    }
    
    user_system = UserLevelSystem(CNT_QUESTION, CNT_CODES)
    
    return jsonify({
        'status': 'started',
        'user_level': user_system.get_user_lvl(),
        'config': {
            'questions_count': CNT_QUESTION,
            'codes_count': CNT_CODES,
            'themes': THEME
        }
    })

@app.route('/api/next_question', methods=['POST'])
def next_question():
    global interview_state
    
    if interview_state['completed']:
        return jsonify({
            'completed': True,
            'total_score': interview_state['total_score'],
            'user_level': user_system.get_user_lvl(),
            'max_score': CNT_QUESTION * 10 + CNT_CODES * 20
        })
    
    if interview_state['current_question_index'] < CNT_QUESTION:
        topic = random.choice(THEME)
        question = sci_box.generate_question(topic, user_system.get_user_lvl())
        
        interview_state['current_question_type'] = 'text'
        interview_state['current_question'] = question
        interview_state['current_topic'] = topic
        
        return jsonify({
            'type': 'text',
            'question': question,
            'topic': topic,
            'difficulty': user_system.get_user_lvl(),
            'progress': {
                'current_question': interview_state['current_question_index'] + 1,
                'total_questions': CNT_QUESTION,
                'current_code': interview_state['current_code_index'],
                'total_codes': CNT_CODES
            }
        })
    
    elif interview_state['current_code_index'] < CNT_CODES:
        topic = random.choice(THEME)
        task = sci_box.generate_coding_task(topic, user_system.get_user_lvl())
        
        interview_state['current_question_type'] = 'code'
        interview_state['current_task'] = task
        interview_state['current_topic'] = topic
        
        return jsonify({
            'type': 'code',
            'task': task,
            'topic': topic,
            'difficulty': user_system.get_user_lvl(),
            'progress': {
                'current_question': CNT_QUESTION,
                'total_questions': CNT_QUESTION,
                'current_code': interview_state['current_code_index'] + 1,
                'total_codes': CNT_CODES
            }
        })
    
    else:
        interview_state['completed'] = True
        return jsonify({
            'completed': True,
            'total_score': interview_state['total_score'],
            'user_level': user_system.get_user_lvl(),
            'max_score': CNT_QUESTION * 10 + CNT_CODES * 20
        })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    global interview_state
    
    data = request.json
    answer = data.get('answer', '')
    
    if interview_state['current_question_type'] != 'text':
        return jsonify({'error': 'No active text question'}), 400
    
    score, explanation = sci_box.evaluate_answer(
        interview_state['current_question'], 
        answer
    )
    
    feedback = sci_box.generate_feedback(
        interview_state['current_question'],
        answer,
        score
    )
    
    interview_state['total_score'] += score
    interview_state['current_question_index'] += 1
    user_system.update_user_lvl(score)
    
    return jsonify({
        'score': score,
        'explanation': explanation,
        'feedback': feedback,
        'total_score': interview_state['total_score'],
        'user_level': user_system.get_user_lvl()
    })

@app.route('/api/submit_code', methods=['POST'])
def submit_code():
    global interview_state
    
    data = request.json
    code = data.get('code', '')
    
    if interview_state['current_question_type'] != 'code':
        return jsonify({'error': 'No active coding task'}), 400
    
    score, detailed_feedback = sci_box.evaluate_code(
        interview_state['current_task'],
        code
    )
    
    additional_feedback = sci_box.generate_code_feedback(
        interview_state['current_task'],
        code
    )
    
    interview_state['total_score'] += score
    interview_state['current_code_index'] += 1
    user_system.update_user_lvl(score)
    
    return jsonify({
        'score': score,
        'detailed_feedback': detailed_feedback,
        'additional_feedback': additional_feedback,
        'total_score': interview_state['total_score'],
        'user_level': user_system.get_user_lvl()
    })

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'running', 
        'message': 'Server is working!',
        'environment': os.getenv('FLASK_ENV', 'development')
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print("=" * 50)
    print("Starting AI Interview Server...")
    print(f"Questions: {CNT_QUESTION}, Code tasks: {CNT_CODES}")
    print(f"Server running on http://{host}:{port}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print("Themes:", THEME)
    print("=" * 50)
    
    # Всегда запускаем встроенный сервер в контейнере
    app.run(host=host, port=port, debug=False, use_reloader=False)


