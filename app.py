from flask import Flask, render_template, request, redirect, url_for, session
from flask_bootstrap import Bootstrap
import sqlite3
import telebot
import time
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from functools import wraps


DATABASE = 'bot_data.db'


BOT_TOKEN = "7714638685:AAEKNyXvkTz2l_ZaKR0Tg7bY-1kp6o-HwPA"  
bot = telebot.TeleBot(BOT_TOKEN)


app = Flask(__name__)
app.secret_key = 'secret_key'  
Bootstrap(app)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with app.open_resource('schema.sql', mode='r') as f:
        conn.executescript(f.read())
    conn.close()

# Создание базы данных 
with app.app_context():
    init_db()


ROLES = {
    'manager': 1,  # Может редактировать ответы бота
    'admin': 2    # Видит статистику и может редактировать ответы
}

def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user_role' not in session or (role and session['user_role'] < role):
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Проверка учетных данных 
        if username == 'manager' and password == 'manager':
            session['user_role'] = ROLES['manager']
            session['username'] = username
            return redirect(url_for('index'))
        elif username == 'admin' and password == 'admin':
            session['user_role'] = ROLES['admin']
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверные учетные данные')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_role', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/', methods=['GET'])
@login_required()
def index():
    return render_template('index.html', username=session['username'])

@app.route('/stats', methods=['GET'])
@login_required()
def stats():
    if session['user_role'] == ROLES['manager']:
        return render_template('access_denied.html', message='Просмотр статистики недоступен для вашей роли.')
    
    conn = get_db_connection()
    try:
        # Статистика по пользователям
        user_stats = pd.read_sql_query("""
            SELECT user_id, COUNT(*) as messages, COUNT(DISTINCT DATE(timestamp)) as days, COUNT(DISTINCT strftime('%Y-%m', timestamp)) as months
            FROM bot_messages
            GROUP BY user_id;
        """, conn)

        # Статистика по командам
        command_stats = pd.read_sql_query("""
            SELECT command, COUNT(*) as count
            FROM bot_messages
            GROUP BY command;
        """, conn)

        
        user_stats_list = user_stats.to_dict(orient='records')
        command_stats_list = command_stats.to_dict(orient='records')

        # График сообщений по дням
        daily_messages = pd.read_sql_query("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM bot_messages
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
        """, conn, index_col='date')

        if not daily_messages.empty:
           plt.figure(figsize=(10, 5))
           plt.plot(daily_messages.index, daily_messages['count'])
           plt.title('Сообщения по дням')
           plt.xlabel('Дата')
           plt.ylabel('Количество сообщений')
           plt.grid(True)

           img = io.BytesIO()
           plt.savefig(img, format='png')
           img.seek(0)
           plot_url = base64.b64encode(img.getvalue()).decode()
           plt.close()
        else:
            plot_url = None


        return render_template('stats.html', user_stats=user_stats_list, command_stats=command_stats_list, plot_url = plot_url)
    except Exception as e:
        return f"Произошла ошибка: {e}"
    finally:
        conn.close()
        
@app.route('/send_message', methods=['GET', 'POST'])
@login_required(role=ROLES['manager'])
def send_message_to_bot():
    if request.method == 'POST':
        chat_id = request.form.get('chat_id')
        message_text = request.form.get('message')
        
        if chat_id and chat_id.isdigit() and message_text:
            try:
                chat_id = int(chat_id)
                bot.send_message(chat_id, message_text)
                conn = get_db_connection()
                conn.execute("INSERT INTO bot_management (chat_id, message, timestamp) VALUES (?, ?, ?)",
                    (chat_id, message_text, datetime.datetime.now()))
                conn.commit()
                conn.close()
                return 'Сообщение отправлено'
            except Exception as e:
                  return f'Ошибка при отправке сообщения: {str(e)}'
        else:
            return 'Неверный chat_id'
    
    return render_template('send_message.html')
    
@app.route('/add_wish', methods=['GET', 'POST'])
@login_required(role=ROLES['manager'])
def add_wish():
    if request.method == 'POST':
        wish_text = request.form.get('wish')
        if wish_text:
            try:
                conn = get_db_connection()
                conn.execute("INSERT INTO wishes (wish) VALUES (?)", (wish_text,))
                conn.commit()
                conn.close()
                return 'Пожелание добавлено'
            except Exception as e:
                return f'Ошибка при добавлении пожелания: {str(e)}'
        else:
            return 'Неверное пожелание'

    return render_template('add_wish.html')


if __name__ == '__main__':
    app.run(debug=True)
