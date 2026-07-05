import telebot
from telebot import types
import json
import os

# ========== НАСТРОЙКИ ==========
TOKEN = '8650355203:AAEUWylsecZQj4AOt26WpnW_Ysxl-Xc4cS4'  # Твой токен
ADMIN_ID = 1208129258  # Твой Telegram ID

bot = telebot.TeleBot(TOKEN)

# ========== ХРАНИЛИЩЕ (JSON) ==========
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'users': {}, 'likes': {}}

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ========== КЛАВИАТУРА ==========
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('📝 Моя анкета', '🔍 Найти команду')
    kb.add('❤️ Мои лайки', '❌ Удалить анкету')
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('📊 Статистика', '📨 Рассылка')
    kb.add('🚫 Бан/Разбан', '📋 Все анкеты')
    kb.add('🔙 Основное меню')
    return kb

# ========== ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    if user_id not in data['users']:
        bot.send_message(message.chat.id, "👋 Привет! Создай анкету через /profile")
    else:
        kb = admin_menu() if user_id == str(ADMIN_ID) else main_menu()
        bot.send_message(message.chat.id, "С возвращением!", reply_markup=kb)

@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = str(message.chat.id)
    if user_id in data['users']:
        u = data['users'][user_id]
        text = (f"📋 Твоя анкета:\n"
                f"Возраст: {u['age']}\n"
                f"Роль: {u['role']}\n"
                f"О себе: {u['about']}")
        kb = admin_menu() if user_id == str(ADMIN_ID) else main_menu()
        bot.send_message(message.chat.id, text, reply_markup=kb)
    else:
        bot.send_message(message.chat.id, "Напиши свой возраст (число):")
        bot.register_next_step_handler(message, get_age)

def get_age(message):
    try:
        age = int(message.text)
        if age < 10 or age > 100:
            raise ValueError
        user_id = str(message.chat.id)
        if user_id not in data['users']:
            data['users'][user_id] = {}
        data['users'][user_id]['age'] = age
        save_data()
        bot.send_message(message.chat.id, "Теперь укажи роль (комбатер/строитель/фармер/помощник):")
        bot.register_next_step_handler(message, get_role)
    except:
        bot.send_message(message.chat.id, "Введи число от 10 до 100.")
        bot.register_next_step_handler(message, get_age)

def get_role(message):
    role = message.text.lower()
    if role not in ['комбатер', 'строитель', 'фармер', 'помощник']:
        bot.send_message(message.chat.id, "Выбери: комбатер, строитель, фармер, помощник")
        bot.register_next_step_handler(message, get_role)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['role'] = role
    save_data()
    bot.send_message(message.chat.id, "Расскажи о себе (или отправь «-»):")
    bot.register_next_step_handler(message, get_about)

def get_about(message):
    about = message.text if message.text != '-' else ''
    user_id = str(message.chat.id)
    data['users'][user_id]['about'] = about
    save_data()
    kb = admin_menu() if user_id == str(ADMIN_ID) else main_menu()
    bot.send_message(message.chat.id, "✅ Анкета создана!", reply_markup=kb)

# ========== КНОПКИ ==========
@bot.message_handler(func=lambda m: m.text == '📝 Моя анкета')
def show_profile(message):
    user_id = str(message.chat.id)
    if user_id in data['users']:
        u = data['users'][user_id]
        text = (f"📋 Твоя анкета:\n"
                f"Возраст: {u['age']}\n"
                f"Роль: {u['role']}\n"
                f"О себе: {u['about']}")
        kb = admin_menu() if user_id == str(ADMIN_ID) else main_menu()
        bot.send_message(message.chat.id, text, reply_markup=kb)
    else:
        bot.send_message(message.chat.id, "У тебя нет анкеты. Напиши /profile")

@bot.message_handler(func=lambda m: m.text == '🔍 Найти команду')
def find_team(message):
    user_id = str(message.chat.id)
    if user_id not in data['users']:
        bot.send_message(message.chat.id, "Сначала создай анкету /profile")
        return
    others = {uid: u for uid, u in data['users'].items() if uid != user_id}
    if not others:
        bot.send_message(message.chat.id, "Пока никого нет.")
        return
    for uid, u in list(others.items())[:3]:
        text = (f"👤 ID: {uid}\n"
                f"Возраст: {u['age']}\n"
                f"Роль: {u['role']}\n"
                f"О себе: {u['about']}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("👍 Лайк", callback_data=f"like_{uid}"))
        bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('like_'))
def like_callback(call):
    from_user = str(call.message.chat.id)
    to_user = call.data.split('_')[1]
    if from_user == to_user:
        bot.answer_callback_query(call.id, "Нельзя лайкнуть себя!")
        return
    if from_user not in data['likes']:
        data['likes'][from_user] = []
    if to_user in data['likes'][from_user]:
        bot.answer_callback_query(call.id, "Ты уже лайкнул.")
        return
    data['likes'][from_user].append(to_user)
    save_data()
    bot.answer_callback_query(call.id, "✅ Лайк!")

    # Проверка взаимности
    if to_user in data['likes'] and from_user in data['likes'][to_user]:
        bot.send_message(call.message.chat.id, f"🎉 Взаимный лайк! Контакт: t.me/{to_user}")
        try:
            bot.send_message(int(to_user), f"🎉 Взаимный лайк! Контакт: t.me/{from_user}")
        except:
            pass

@bot.message_handler(func=lambda m: m.text == '❤️ Мои лайки')
def my_likes(message):
    user_id = str(message.chat.id)
    liked = data['likes'].get(user_id, [])
    if not liked:
        bot.send_message(message.chat.id, "Ты никого не лайкнул.", reply_markup=main_menu())
        return
    text = "Ты лайкнул:\n"
    for uid in liked:
        if uid in data['users']:
            u = data['users'][uid]
            text += f"ID: {uid} (Возраст: {u['age']}, Роль: {u['role']})\n"
        else:
            text += f"ID: {uid}\n"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '❌ Удалить анкету')
def delete_profile(message):
    user_id = str(message.chat.id)
    if user_id in data['users']:
        del data['users'][user_id]
        save_data()
        bot.send_message(message.chat.id, "❌ Анкета удалена.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "У тебя нет анкеты.")

# ========== АДМИН-ФУНКЦИИ ==========
@bot.message_handler(func=lambda m: m.text == '📊 Статистика' and str(m.chat.id) == str(ADMIN_ID))
def admin_stats(message):
    users = len(data['users'])
    likes = sum(len(v) for v in data['likes'].values())
    bot.send_message(message.chat.id, f"📊 Статистика:\nПользователей: {users}\nЛайков: {likes}", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == '📨 Рассылка' and str(m.chat.id) == str(ADMIN_ID))
def admin_broadcast(message):
    msg = bot.send_message(message.chat.id, "Введи текст для рассылки:")
    bot.register_next_step_handler(msg, broadcast_send)

def broadcast_send(message):
    text = message.text
    sent = 0
    for uid in data['users']:
        try:
            bot.send_message(int(uid), f"📢 {text}")
            sent += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ Отправлено {sent} пользователям.", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == '📋 Все анкеты' and str(m.chat.id) == str(ADMIN_ID))
def admin_all_users(message):
    if not data['users']:
        bot.send_message(message.chat.id, "Нет пользователей.", reply_markup=admin_menu())
        return
    text = "📋 Все пользователи:\n"
    for uid, u in data['users'].items():
        text += f"ID: {uid}, {u['age']} лет, {u['role']}\n"
    bot.send_message(message.chat.id, text, reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == '🔙 Основное меню' and str(m.chat.id) == str(ADMIN_ID))
def back_to_main(message):
    bot.send_message(message.chat.id, "Основное меню:", reply_markup=main_menu())

print("✅ Бот запущен!")
bot.infinity_polling()