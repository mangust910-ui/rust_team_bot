import telebot
from telebot import types
import json
import os
import re

TOKEN = '8650355203:AAEUWylsecZQj4AOt26WpnW_Ysxl-Xc4cS4'
ADMIN_ID = 1208129258

bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'users': {}, 'likes': {}, 'banned': [], 'search_results': [], 'search_offset': 0}

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ================== КЛАВИАТУРЫ ==================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('📝 Моя анкета', '✏️ Редактировать')
    kb.add('🔍 Поиск', '❤️ Лайки/Матчи')
    kb.add('❌ Удалить анкету', '🆘 Поддержка')
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('📊 Статистика', '📨 Рассылка')
    kb.add('🚫 Бан/Разбан', '📋 Все анкеты')
    kb.add('🔙 Основное меню')
    return kb

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def get_user(user_id):
    return data['users'].get(str(user_id))

def user_exists(user_id):
    return str(user_id) in data['users']

def is_banned(user_id):
    return str(user_id) in data.get('banned', [])

def format_profile(user_id, show_id=False):
    u = get_user(user_id)
    if not u:
        return "Анкета не найдена."
    text = f"👤 {u.get('username', 'Без username')}\n"
    text += f"📅 Возраст: {u.get('age', 'Не указан')}\n"
    text += f"🕒 Часы в игре: {u.get('hours', 'Не указано')}\n"
    text += f"⚔️ PvP-скилл: {u.get('skill', 'Не указан')}\n"
    text += f"🎯 Роли: {u.get('roles', 'Не указаны')}\n"
    text += f"🗣 Язык: {u.get('lang', 'Не указан')}\n"
    text += f"🎙 Голосовой чат: {u.get('voice', 'Не указан')}\n"
    text += f"⏰ Часовой пояс: {u.get('timezone', 'Не указан')}\n"
    text += f"📆 Время игры: {u.get('playtime', 'Не указано')}\n"
    text += f"⏳ Сессия: {u.get('session', 'Не указана')}\n"
    text += f"📝 О себе: {u.get('about', 'Не указано')}"
    if show_id:
        text += f"\n🆔 ID: {user_id}"
    return text

def add_like(from_user, to_user):
    if from_user not in data['likes']:
        data['likes'][from_user] = []
    if to_user not in data['likes'][from_user]:
        data['likes'][from_user].append(to_user)
        save_data()
        return True
    return False

def get_mutual_likes(user_id):
    user_id = str(user_id)
    result = []
    if user_id in data['likes']:
        for liked in data['likes'][user_id]:
            if liked in data['likes'] and user_id in data['likes'][liked]:
                result.append(liked)
    return result

def get_my_likes(user_id):
    return data['likes'].get(str(user_id), [])

# ================== ОБРАБОТЧИКИ КОМАНД ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены и не можете использовать бота.")
        return
    if not user_exists(user_id):
        bot.send_message(message.chat.id, "👋 Привет! Давай создадим анкету. Напиши /profile")
        return
    kb = admin_menu() if is_admin(user_id) else main_menu()
    bot.send_message(message.chat.id, "С возвращением!", reply_markup=kb)

@bot.message_handler(commands=['profile'])
def profile_start(message):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return
    if user_exists(user_id):
        show_profile(message)
    else:
        bot.send_message(message.chat.id, "Давай создадим анкету. Укажи свой возраст (целое число):")
        bot.register_next_step_handler(message, get_age)

# ================== РЕГИСТРАЦИЯ ==================
def get_age(message):
    try:
        age = int(message.text)
        if age < 10 or age > 100:
            raise ValueError
        user_id = str(message.chat.id)
        if user_id not in data['users']:
            data['users'][user_id] = {}
        data['users'][user_id]['age'] = age
        data['users'][user_id]['username'] = message.from_user.username or ''
        save_data()
        bot.send_message(message.chat.id, "Сколько часов наиграл? (0-50 / 50-200 / 200-500 / 500+)")
        bot.register_next_step_handler(message, get_hours)
    except:
        bot.send_message(message.chat.id, "Введи число от 10 до 100.")
        bot.register_next_step_handler(message, get_age)

def get_hours(message):
    val = message.text
    if val not in ['0-50', '50-200', '200-500', '500+']:
        bot.send_message(message.chat.id, "Выбери: 0-50, 50-200, 200-500, 500+")
        bot.register_next_step_handler(message, get_hours)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['hours'] = val
    save_data()
    bot.send_message(message.chat.id, "Оцени PvP-скилл (новичок / средний / опытный / профессионал):")
    bot.register_next_step_handler(message, get_skill)

def get_skill(message):
    val = message.text
    if val not in ['новичок', 'средний', 'опытный', 'профессионал']:
        bot.send_message(message.chat.id, "Выбери: новичок, средний, опытный, профессионал")
        bot.register_next_step_handler(message, get_skill)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['skill'] = val
    save_data()
    bot.send_message(message.chat.id, "Выбери роли (через запятую): комбатер, строитель, фармер, помощник руководителя")
    bot.register_next_step_handler(message, get_roles)

def get_roles(message):
    text = message.text
    roles = [r.strip() for r in text.split(',')]
    allowed = ['комбатер', 'строитель', 'фармер', 'помощник руководителя']
    if not all(r in allowed for r in roles):
        bot.send_message(message.chat.id, "Допустимые роли: комбатер, строитель, фармер, помощник руководителя")
        bot.register_next_step_handler(message, get_roles)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['roles'] = ', '.join(roles)
    save_data()
    bot.send_message(message.chat.id, "Язык общения (русский / английский / другой):")
    bot.register_next_step_handler(message, get_lang)

def get_lang(message):
    val = message.text
    if val not in ['русский', 'английский', 'другой']:
        bot.send_message(message.chat.id, "Выбери: русский, английский или другой")
        bot.register_next_step_handler(message, get_lang)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['lang'] = val
    save_data()
    bot.send_message(message.chat.id, "Голосовой чат? (да / нет)")
    bot.register_next_step_handler(message, get_voice)

def get_voice(message):
    val = message.text
    if val not in ['да', 'нет']:
        bot.send_message(message.chat.id, "Ответь да или нет")
        bot.register_next_step_handler(message, get_voice)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['voice'] = val
    save_data()
    bot.send_message(message.chat.id, "Часовой пояс (например, +3 или -5):")
    bot.register_next_step_handler(message, get_timezone)

def get_timezone(message):
    tz = message.text.strip()
    if not re.match(r'^[+-]?\d+$', tz):
        bot.send_message(message.chat.id, "Введи в формате +3 или -5")
        bot.register_next_step_handler(message, get_timezone)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['timezone'] = tz
    save_data()
    bot.send_message(message.chat.id, "Когда играешь? (утро, день, вечер, ночь, будни, выходные – через запятую)")
    bot.register_next_step_handler(message, get_playtime)

def get_playtime(message):
    text = message.text
    parts = [p.strip() for p in text.split(',')]
    allowed = ['утро', 'день', 'вечер', 'ночь', 'будни', 'выходные']
    if not all(p in allowed for p in parts):
        bot.send_message(message.chat.id, "Допустимые: утро, день, вечер, ночь, будни, выходные")
        bot.register_next_step_handler(message, get_playtime)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['playtime'] = ', '.join(parts)
    save_data()
    bot.send_message(message.chat.id, "Длительность сессии (1-2ч / 2-4ч / 4+ч):")
    bot.register_next_step_handler(message, get_session)

def get_session(message):
    val = message.text
    if val not in ['1-2ч', '2-4ч', '4+ч']:
        bot.send_message(message.chat.id, "Выбери: 1-2ч, 2-4ч или 4+ч")
        bot.register_next_step_handler(message, get_session)
        return
    user_id = str(message.chat.id)
    data['users'][user_id]['session'] = val
    save_data()
    bot.send_message(message.chat.id, "Расскажи о себе (можно пропустить, отправь «-»):")
    bot.register_next_step_handler(message, get_about)

def get_about(message):
    about = message.text if message.text != '-' else ''
    user_id = str(message.chat.id)
    data['users'][user_id]['about'] = about
    save_data()
    kb = admin_menu() if is_admin(user_id) else main_menu()
    bot.send_message(message.chat.id, "✅ Анкета создана!", reply_markup=kb)

# ================== ПОКАЗ АНКЕТЫ ==================
@bot.message_handler(func=lambda m: m.text == '📝 Моя анкета')
def show_profile(message):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return
    if not user_exists(user_id):
        bot.send_message(message.chat.id, "У тебя нет анкеты. Напиши /profile")
        return
    text = format_profile(user_id, show_id=is_admin(user_id))
    kb = admin_menu() if is_admin(user_id) else main_menu()
    bot.send_message(message.chat.id, text, reply_markup=kb)

# ================== РЕДАКТИРОВАНИЕ ==================
@bot.message_handler(func=lambda m: m.text == '✏️ Редактировать')
def edit_profile_start(message):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return
    if not user_exists(user_id):
        bot.send_message(message.chat.id, "У тебя нет анкеты.")
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Возраст", callback_data="edit_age"))
    kb.add(types.InlineKeyboardButton("Часы", callback_data="edit_hours"))
    kb.add(types.InlineKeyboardButton("Скилл", callback_data="edit_skill"))
    kb.add(types.InlineKeyboardButton("Роли", callback_data="edit_roles"))
    kb.add(types.InlineKeyboardButton("Язык", callback_data="edit_lang"))
    kb.add(types.InlineKeyboardButton("Голос", callback_data="edit_voice"))
    kb.add(types.InlineKeyboardButton("Таймзона", callback_data="edit_timezone"))
    kb.add(types.InlineKeyboardButton("Время игры", callback_data="edit_playtime"))
    kb.add(types.InlineKeyboardButton("Сессия", callback_data="edit_session"))
    kb.add(types.InlineKeyboardButton("О себе", callback_data="edit_about"))
    kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="edit_cancel"))
    bot.send_message(message.chat.id, "Выбери поле для редактирования:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
def edit_callback(call):
    user_id = str(call.message.chat.id)
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "Вы забанены.")
        return
    field = call.data.split('_')[1]
    if field == 'cancel':
        bot.edit_message_text("Отменено.", call.message.chat.id, call.message.message_id)
        return
    bot.edit_message_text(f"Введи новое значение для поля '{field}':", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, lambda m: save_edit(m, field))

def save_edit(message, field):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return
    if not user_exists(user_id):
        bot.send_message(message.chat.id, "Анкета не найдена.")
        return
    new_val = message.text
    # Валидация
    if field == 'age':
        try:
            new_val = int(new_val)
            if new_val < 10 or new_val > 100:
                raise ValueError
        except:
            bot.send_message(message.chat.id, "Введи число от 10 до 100.")
            return
    elif field == 'hours':
        if new_val not in ['0-50', '50-200', '200-500', '500+']:
            bot.send_message(message.chat.id, "Выбери: 0-50, 50-200, 200-500, 500+")
            return
    elif field == 'skill':
        if new_val not in ['новичок', 'средний', 'опытный', 'профессионал']:
            bot.send_message(message.chat.id, "Выбери: новичок, средний, опытный, профессионал")
            return
    elif field == 'roles':
        roles = [r.strip() for r in new_val.split(',')]
        allowed = ['комбатер', 'строитель', 'фармер', 'помощник руководителя']
        if not all(r in allowed for r in roles):
            bot.send_message(message.chat.id, "Допустимые роли: комбатер, строитель, фармер, помощник руководителя")
            return
        new_val = ', '.join(roles)
    elif field == 'lang':
        if new_val not in ['русский', 'английский', 'другой']:
            bot.send_message(message.chat.id, "Выбери: русский, английский или другой")
            return
    elif field == 'voice':
        if new_val not in ['да', 'нет']:
            bot.send_message(message.chat.id, "Ответь да или нет")
            return
    elif field == 'timezone':
        if not re.match(r'^[+-]?\d+$', new_val):
            bot.send_message(message.chat.id, "Введи в формате +3 или -5")
            return
    elif field == 'playtime':
        parts = [p.strip() for p in new_val.split(',')]
        allowed = ['утро', 'день', 'вечер', 'ночь', 'будни', 'выходные']
        if not all(p in allowed for p in parts):
            bot.send_message(message.chat.id, "Допустимые: утро, день, вечер, ночь, будни, выходные")
            return
        new_val = ', '.join(parts)
    elif field == 'session':
        if new_val not in ['1-2ч', '2-4ч', '4+ч']:
            bot.send_message(message.chat.id, "Выбери: 1-2ч, 2-4ч или 4+ч")
            return
    elif field == 'about':
        pass  # любое значение
    data['users'][user_id][field] = new_val
    save_data()
    kb = admin_menu() if is_admin(user_id) else main_menu()
    bot.send_message(message.chat.id, f"✅ Поле '{field}' обновлено!", reply_markup=kb)

# ================== ПОИСК С ФИЛЬТРАМИ ==================
@bot.message_handler(func=lambda m: m.text == '🔍 Поиск')
def search_start(message):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return
    if not user_exists(user_id):
        bot.send_message(message.chat.id, "Сначала создай анкету /profile")
        return
    msg = bot.send_message(message.chat.id, "Выбери фильтры (можно пропустить).\nЧасы в игре: 0-50, 50-200, 200-500, 500+ (напиши вариант или 'пропустить')")
    bot.register_next_step_handler(msg, filter_hours, {})

def filter_hours(message, filters):
    val = message.text.lower()
    if val != 'пропустить' and val not in ['0-50', '50-200', '200-500', '500+']:
        bot.send_message(message.chat.id, "Выбери: 0-50, 50-200, 200-500, 500+ или 'пропустить'")
        bot.register_next_step_handler(message, filter_hours, filters)
        return
    if val != 'пропустить':
        filters['hours'] = val
    msg = bot.send_message(message.chat.id, "PvP-скилл: новичок, средний, опытный, профессионал (или 'пропустить')")
    bot.register_next_step_handler(msg, filter_skill, filters)

def filter_skill(message, filters):
    val = message.text.lower()
    if val != 'пропустить' and val not in ['новичок', 'средний', 'опытный', 'профессионал']:
        bot.send_message(message.chat.id, "Выбери: новичок, средний, опытный, профессионал или 'пропустить'")
        bot.register_next_step_handler(message, filter_skill, filters)
        return
    if val != 'пропустить':
        filters['skill'] = val
    msg = bot.send_message(message.chat.id, "Роли (через запятую): комбатер, строитель, фармер, помощник руководителя (или 'пропустить')")
    bot.register_next_step_handler(msg, filter_roles, filters)

def filter_roles(message, filters):
    val = message.text.lower()
    if val != 'пропустить':
        roles = [r.strip() for r in val.split(',')]
        allowed = ['комбатер', 'строитель', 'фармер', 'помощник руководителя']
        if not all(r in allowed for r in roles):
            bot.send_message(message.chat.id, "Допустимые роли: комбатер, строитель, фармер, помощник руководителя")
            bot.register_next_step_handler(message, filter_roles, filters)
            return
        filters['roles'] = roles
    msg = bot.send_message(message.chat.id, "Язык: русский, английский, другой (или 'пропустить')")
    bot.register_next_step_handler(msg, filter_lang, filters)

def filter_lang(message, filters):
    val = message.text.lower()
    if val != 'пропустить' and val not in ['русский', 'английский', 'другой']:
        bot.send_message(message.chat.id, "Выбери: русский, английский, другой или 'пропустить'")
        bot.register_next_step_handler(message, filter_lang, filters)
        return
    if val != 'пропустить':
        filters['lang'] = val
    msg = bot.send_message(message.chat.id, "Голосовой чат: да, нет (или 'пропустить')")
    bot.register_next_step_handler(msg, filter_voice, filters)

def filter_voice(message, filters):
    val = message.text.lower()
    if val != 'пропустить' and val not in ['да', 'нет']:
        bot.send_message(message.chat.id, "Выбери: да, нет или 'пропустить'")
        bot.register_next_step_handler(message, filter_voice, filters)
        return
    if val != 'пропустить':
        filters['voice'] = val
    msg = bot.send_message(message.chat.id, "Минимальный возраст (число или 'пропустить'):")
    bot.register_next_step_handler(msg, filter_age_min, filters)

def filter_age_min(message, filters):
    val = message.text.lower()
    if val != 'пропустить':
        try:
            filters['age_min'] = int(val)
        except:
            bot.send_message(message.chat.id, "Введи число или 'пропустить'")
            bot.register_next_step_handler(message, filter_age_min, filters)
            return
    msg = bot.send_message(message.chat.id, "Максимальный возраст (число или 'пропустить'):")
    bot.register_next_step_handler(msg, filter_age_max, filters)

def filter_age_max(message, filters):
    val = message.text.lower()
    if val != 'пропустить':
        try:
            filters['age_max'] = int(val)
        except:
            bot.send_message(message.chat.id, "Введи число или 'пропустить'")
            bot.register_next_step_handler(message, filter_age_max, filters)
            return
    # Применяем фильтры
    user_id = str(message.chat.id)
    results = []
    for uid, u in data['users'].items():
        if uid == user_id:
            continue
        match = True
        if 'hours' in filters and u.get('hours') != filters['hours']:
            match = False
        if 'skill' in filters and u.get('skill') != filters['skill']:
            match = False
        if 'roles' in filters:
            user_roles = [r.strip() for r in u.get('roles', '').split(',')]
            if not any(r in user_roles for r in filters['roles']):
                match = False
        if 'lang' in filters and u.get('lang') != filters['lang']:
            match = False
        if 'voice' in filters and u.get('voice') != filters['voice']:
            match = False
        if 'age_min' in filters and u.get('age', 0) < filters['age_min']:
            match = False
        if 'age_max' in filters and u.get('age', 0) > filters['age_max']:
            match = False
        if match:
            results.append(uid)
    if not results:
        bot.send_message(message.chat.id, "По вашему запросу никого не найдено.", reply_markup=main_menu())
        return
    data['search_results'] = results
    data['search_offset'] = 0
    save_data()
    show_results(message, results, 0)

def show_results(message, results, offset):
    user_id = str(message.chat.id)
    if offset >= len(results):
        bot.send_message(message.chat.id, "Больше нет анкет.", reply_markup=main_menu())
        return
    uid = results[offset]
    text = format_profile(uid, show_id=is_admin(user_id))
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("👍 Лайк", callback_data=f"like_{uid}"))
    if offset + 1 < len(results):
        kb.add(types.InlineKeyboardButton("➡️ Далее", callback_data=f"next_{offset+1}"))
    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('next_'))
def next_result(call):
    offset = int(call.data.split('_')[1])
    results = data.get('search_results', [])
    if offset < len(results):
        show_results(call.message, results, offset)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Больше нет анкет.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('like_'))
def like_callback(call):
    from_user = str(call.message.chat.id)
    to_user = call.data.split('_')[1]
    if from_user == to_user:
        bot.answer_callback_query(call.id, "Нельзя лайкнуть себя!")
        return
    if is_banned(from_user):
        bot.answer_callback_query(call.id, "Вы забанены.")
        return
    if add_like(from_user, to_user):
        bot.answer_callback_query(call.id, "✅ Лайк поставлен!")
        # Проверка взаимности
        mutual = get_mutual_likes(from_user)
        if to_user in mutual:
            username_from = data['users'].get(from_user, {}).get('username', '')
            username_to = data['users'].get(to_user, {}).get('username', '')
            contact_from = f"@{username_from}" if username_from else "без username"
            contact_to = f"@{username_to}" if username_to else "без username"
            bot.send_message(call.message.chat.id, f"🎉 Взаимный лайк! Контакт: {contact_to}")
            try:
                bot.send_message(int(to_user), f"🎉 Взаимный лайк! Контакт: {contact_from}")
            except:
                pass
    else:
        bot.answer_callback_query(call.id, "Ты уже лайкнул этого пользователя.")

# ================== ЛАЙКИ/МАТЧИ ==================
@bot.message_handler(func=lambda m: m.text == '❤️ Лайки/Матчи')
def my_likes(message):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return
    liked = get_my_likes(user_id)
    mutual = get_mutual_likes(user_id)
    text = f"Ты лайкнул: {len(liked)} пользователей.\nВзаимных лайков: {len(mutual)}."
    if mutual:
        text += "\nКонтакты взаимных:\n"
        for uid in mutual:
            u = data['users'].get(uid, {})
            username = u.get('username', '')
            text += f"@{username}" if username else f"ID {uid} (без username)"
            text += "\n"
    kb = admin_menu() if is_admin(user_id) else main_menu()
    bot.send_message(message.chat.id, text, reply_markup=kb)

# ================== УДАЛЕНИЕ ==================
@bot.message_handler(func=lambda m: m.text == '❌ Удалить анкету')
def delete_profile(message):
    user_id = str(message.chat.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return
    if user_exists(user_id):
        del data['users'][user_id]
        save_data()
        bot.send_message(message.chat.id, "❌ Анкета удалена.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "У тебя нет анкеты.")

# ================== ПОДДЕРЖКА ==================
@bot.message_handler(func=lambda m: m.text == '🆘 Поддержка')
def support(message):
    bot.send_message(message.chat.id, "🆘 По вопросам обращайтесь к @Man_Gust_Official")

# ================== АДМИН-ФУНКЦИИ ==================
@bot.message_handler(func=lambda m: m.text == '📊 Статистика' and is_admin(m.chat.id))
def admin_stats(message):
    users = len(data['users'])
    likes = sum(len(v) for v in data['likes'].values())
    banned = len(data.get('banned', []))
    bot.send_message(message.chat.id, f"📊 Статистика:\nПользователей: {users}\nЛайков: {likes}\nЗабанено: {banned}", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == '📨 Рассылка' and is_admin(m.chat.id))
def admin_broadcast_start(message):
    msg = bot.send_message(message.chat.id, "Введите текст рассылки:")
    bot.register_next_step_handler(msg, admin_broadcast_send)

def admin_broadcast_send(message):
    text = message.text
    sent = 0
    for uid in data['users']:
        try:
            bot.send_message(int(uid), f"📢 {text}")
            sent += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ Отправлено {sent} пользователям.", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == '🚫 Бан/Разбан' and is_admin(m.chat.id))
def admin_ban_start(message):
    msg = bot.send_message(message.chat.id, "Введите ID пользователя для бана/разбана:")
    bot.register_next_step_handler(msg, admin_ban_id)

def admin_ban_id(message):
    try:
        target = int(message.text)
    except:
        bot.send_message(message.chat.id, "Введите число.")
        return
    if str(target) in data['users']:
        if str(target) in data.get('banned', []):
            bot.send_message(message.chat.id, f"Пользователь {target} уже забанен. Разбанить? (да/нет)")
            bot.register_next_step_handler(message, lambda m: admin_unban_confirm(m, target))
        else:
            bot.send_message(message.chat.id, f"Пользователь {target} не забанен. Забанить? (да/нет)")
            bot.register_next_step_handler(message, lambda m: admin_ban_confirm(m, target))
    else:
        bot.send_message(message.chat.id, f"Пользователь {target} не найден в базе.")

def admin_ban_confirm(message, target):
    if message.text.lower() == 'да':
        if 'banned' not in data:
            data['banned'] = []
        if target not in data['banned']:
            data['banned'].append(target)
            save_data()
            bot.send_message(message.chat.id, f"✅ Пользователь {target} забанен.", reply_markup=admin_menu())
        else:
            bot.send_message(message.chat.id, "Пользователь уже в бане.", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=admin_menu())

def admin_unban_confirm(message, target):
    if message.text.lower() == 'да':
        if 'banned' in data and target in data['banned']:
            data['banned'].remove(target)
            save_data()
            bot.send_message(message.chat.id, f"✅ Пользователь {target} разбанен.", reply_markup=admin_menu())
        else:
            bot.send_message(message.chat.id, "Пользователь не в бане.", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, "Действие отменено.", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == '📋 Все анкеты' and is_admin(m.chat.id))
def admin_all_users(message):
    if not data['users']:
        bot.send_message(message.chat.id, "Нет пользователей.", reply_markup=admin_menu())
        return
    text = "📋 Все пользователи:\n"
    for uid, u in data['users'].items():
        text += f"ID: {uid}, @{u.get('username', 'нет')}, {u.get('age', '?')} лет, {u.get('roles', '')}\n"
    bot.send_message(message.chat.id, text, reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == '🔙 Основное меню' and is_admin(m.chat.id))
def back_to_main(message):
    bot.send_message(message.chat.id, "Основное меню:", reply_markup=main_menu())

# ================== ЗАПУСК ==================
print("✅ Бот запущен!")
bot.infinity_polling()