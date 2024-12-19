import telebot
import random
import schedule
import time
from threading import Thread
from datetime import datetime
import sqlite3


DATABASE = 'bot_data.db'

BOT_TOKEN = "7714638685:AAEKNyXvkTz2l_ZaKR0Tg7bY-1kp6o-HwPA"
bot = telebot.TeleBot(BOT_TOKEN)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def log_message(message, command=None, game=None):
    user_id = message.chat.id
    username = message.from_user.username
    text = message.text
    timestamp = datetime.now()
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO bot_messages (user_id, username, message, timestamp, command, game)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, text, timestamp, command, game))
        conn.commit()
    except sqlite3.Error as err:
        print(f"Ошибка записи в базу данных: {err}")
    finally:
        conn.close()
@bot.message_handler(commands=['start'])
def start_message(message):
    greetings = [
        "зачем стартуешь, делать нечего?",
        "очень не рад тебя тут видеть, но можешь остаться",
        "склонись перед величием чат-бота",
        "ты попал в место, где логика отдыхает"
    ]
    greeting = random.choice(greetings)
    bot.reply_to(message, f'Приветствую тебя, человечишко, {greeting}')
    log_message(message, command='/start')


def send_random_fact(message):
    chat_id = message.chat.id
    if chat_id:
        with open("абсурдные_факты.txt", "r", encoding="utf-8") as f:
            факты = f.readlines()
        факт = random.choice(факты).strip()
        bot.send_message(chat_id, факт)
        log_message(message, command='random_fact')

schedule.every().day.at("08:00").do(lambda: send_random_fact(last_message))
schedule.every().day.at("12:00").do(lambda: send_random_fact(last_message))
schedule.every().day.at("18:00").do(lambda: send_random_fact(last_message))
schedule.every().day.at("20:00").do(lambda: send_random_fact(last_message))


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


Thread(target=run_schedule).start()

# Слова для игры 1
слова_game1 = [
    "ёлки-палки", "Сандаль", "Тракторина", "Медовуха", "Негр-вампир",
    "Йогурт", "Шепоток", "Пипидастр", "Мухосранск", "Барабулька",
    "Боеголовка", "Московский авиационный институт", "Выхухоль", "Харчо", "Гондола",
    "Чечевица", "Бульдозер", "Рододендрон", "Пюпитр", "Тарталетка"
]

# Слова для игры 2
words_game2 = ["кукарача", "пердимонокль", "сколопендра", "перогрыз", "чупакабра", "дранулет"]

@bot.message_handler(commands=['game1'])
def start_game1(message):
    user_data[message.chat.id] = {"game1_started": True, "last_word": ""}
    bot.reply_to(message, "Игра началась! Чтобы завершить игру напиши 'ты не умеешь играть в слова'")
    bot.reply_to(message, "Напиши любое слово:")
    log_message(message, command='/game1', game='game1')

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["game1_started"])
def play_word_game1(message):
    chat_id = message.chat.id
    if message.text.lower() == "ты не умеешь играть в слова":
        user_data[chat_id]["game1_started"] = False
        bot.reply_to(message, "Сам дурак, это ты играть не умеешь! До встречи в следующей игре!")
        log_message(message, command='game1_stop', game='game1')
        return
    
    user_word = message.text
    last_bot_word = user_data[chat_id].get("last_word", "")
    
    if last_bot_word:
      if user_word[0].lower() != last_bot_word[-1].lower():
          bot.reply_to(message, "Надо начинать слово на последнюю букву предыдущего слова!")
          log_message(message, command='game1_invalid_move', game='game1')
          return
        
    bot_word = random.choice(слова_game1)
    bot.reply_to(message, bot_word)
    user_data[chat_id]["last_word"] = bot_word
    log_message(message, command='game1_move', game='game1')


game2_data = {}


@bot.message_handler(commands=['game2'])
def start_game2(message):
    word = random.choice(words_game2)
    hidden_word = ["_"] * len(word)
    game2_data[message.chat.id] = {"word": word, "hidden_word": hidden_word, "attempts": 0, "guessed_letters": set(), "game2_started": True}
    bot.reply_to(message, f"Я загадал слово: {' '.join(hidden_word)}. Попробуй угадать буквы!")
    log_message(message, command='/game2', game='game2')


@bot.message_handler(func=lambda message: message.chat.id in game2_data and game2_data[message.chat.id]["game2_started"] )
def play_game2(message):
    chat_id = message.chat.id
    data = game2_data[chat_id]
    letter = message.text.lower()
    
    if len(letter) != 1 or not letter.isalpha():
        bot.reply_to(message, "Введите одну букву.")
        log_message(message, command='game2_invalid_move', game='game2')
        return
    
    if letter in data["guessed_letters"]:
        bot.reply_to(message, "Вы уже называли эту букву. Попробуйте другую.")
        log_message(message, command='game2_repeated_move', game='game2')
        return
        
    data["guessed_letters"].add(letter)
    data["attempts"] += 1
    
    if letter in data["word"]:
        for idx, char in enumerate(data["word"]):
            if char == letter:
                data["hidden_word"][idx] = letter
        bot.reply_to(message, f"Отлично! {' '.join(data['hidden_word'])}")
        log_message(message, command='game2_correct_move', game='game2')
    else:
        bot.reply_to(message, "Нет такой буквы. Подсказка: слово бредовое.")
        log_message(message, command='game2_incorrect_move', game='game2')
    
    if "_" not in data["hidden_word"]:
        bot.reply_to(message, f"Поздравляю! Вы отгадали слово '{data['word']}' за {data['attempts']} попыток.")
        log_message(message, command='game2_win', game='game2')
        del game2_data[chat_id]
        
@bot.message_handler(commands=['stop'])
def stop_game2(message):
    if message.chat.id in game2_data:
        game2_data[message.chat.id]["game2_started"] = False
        del game2_data[message.chat.id]
        bot.reply_to(message, "Игра остановлена. Напишите '/game2', чтобы начать заново.")
        log_message(message, command='/stop', game='game2')
@bot.message_handler(commands=['help'])
def help_message(message):
    myhelp = (
        "/start - Начало работы бота\n"
        "/help - Помощь\n"
        "/game1 - Игра в бредослова\n"
        "/game2 - игра Угадай слово\n"
        "/wish - Получить пожелание"
    )
    bot.reply_to(message, f'Я умею:\n{myhelp}')
    log_message(message, command='/help')
    
@bot.message_handler(commands=['wish'])
def send_wish(message):
    conn = get_db_connection()
    try:
        wishes = conn.execute("SELECT wish FROM wishes").fetchall()
        if wishes:
            wish = random.choice([row['wish'] for row in wishes])
            bot.reply_to(message, wish)
            log_message(message, command='/wish')
        else:
            bot.reply_to(message, "Пока нет пожеланий в базе данных.")
            log_message(message, command='/wish_empty')
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")
        log_message(message, command='/wish_error', game=str(e))
    finally:
        conn.close()

last_message = None
user_data = {}

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global last_message
    last_message = message
    if not message.text.startswith('/'):
         log_message(message)

bot.polling(none_stop=True)