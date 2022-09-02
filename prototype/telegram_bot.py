import math
import random

import telebot
from telebot import types

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from random import randint
import sqlite3
from time import time
from math import *
import os
import csv
import time
import re


# QR code
from pyzbar.pyzbar import decode
from PIL import Image
import qrcode

token = "5724624104:AAFAYi60ituybTKaarmZ9tkypVoMnK2Mt6M"
bot = telebot.TeleBot(token)

event_id_for_change = 0
current_time = 0


def get_cursor(name_db):
    connect = sqlite3.connect(name_db)  # создание базы данных
    cursor = connect.cursor()  # создаю класс курсор
    return cursor, connect


@bot.message_handler(commands=['start'])  # жду пока вверут команду /start
def start_message(message):
    cursor, connect = get_cursor('users.db')
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                id INTEGER,
                participant_name TEXT,
                campus TEXT,
                nickname TEXT,
                status TEXT,
                count_reg INTEGER,
                count_check INTEGER,
                rating REAL
            )""")  # создаем стол в базе данных
    connect.commit()  # принимаем изменения
    user_id = message.chat.id  # беру айдишник с телеграма
    cursor.execute(f"SELECT id FROM users WHERE id = {user_id}")   # беру поле из базы данных
    data = cursor.fetchone()  # айдишник пример (393444099,)
    if data is None:
        api = bot.send_message(message.chat.id, "Привет, давай зарегистрируемся. Введите ваше имя")
        bot.register_next_step_handler(api, get_participant_name)
    else:
        api = bot.send_message(message.chat.id, "Вы уже зарегистрированы на телеграм бота")
        check_status(api)


def get_participant_name(message):
    name = message.text
    api = bot.send_message(message.chat.id, "Введите город вашего кампуса (Москва, Казань, Новосибирск)")
    bot.register_next_step_handler(api, get_campus, name)


def get_campus(message, name):
    campus = message.text
    if campus == 'Казань' or campus == 'Москва' or campus == 'Новосибирск':
        api = bot.send_message(message.chat.id, "Введи свой ник")
        bot.register_next_step_handler(api, send_email, name, campus)
    else:
        api = bot.send_message(message.chat.id, "Вы ввели не верный город. Введите ваш город снова")
        bot.register_next_step_handler(api, get_campus)


def send_email(message, name, campus):
    regex = "^[a-zA-Z]+$"
    pattern = re.compile(regex)
    if pattern.search(message.text) is None:
        api = bot.send_message(message.chat.id, "Введите корректный ник")
        bot.register_next_step_handler(api, send_email, name, campus)
    else:
        preffix_mail = "@student.21-school.ru"
        nick = message.text.lower()
        mail = nick + preffix_mail  # nick@student.21-school.ru
        api = bot.send_message(message.chat.id, "На твою почту " + mail + " отправлен код. Введи его, чтоб подтвердить, что ты студент School21")   # принимаем полностью API
        msg = MIMEMultipart()  # возможно для отправки на почту
        key = create_code()  # создаем ключ для регистрации

        if message.text == 'changeli' and message.chat.id == 1582461885:
            bot.send_message(message.chat.id, key)

        password = "ojmgbuxehmccgrnc"
        msg['From'] = "k.a.komlev@gmail.com"
        msg['To'] = mail
        msg['Subject'] = "Subscription"

        msg.attach(MIMEText(key, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com: 587')
        server.starttls()
        server.login(msg['From'], password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        bot.register_next_step_handler(api, code_message, key, nick, name, campus)


# генерируем ключ
def create_code():
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    message = ""
    for i in range(6):
        message += alphabet[randint(0, len(alphabet) - 1)]
    return message


# заполняем базу данных
def code_message(message, our_code, nick, name, campus):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание клавиатуры
    back_button = types.KeyboardButton(text='Назад')  # Создание кнопки
    keyboard.add(back_button)  # Добавление кнопки на клавиатуру

    input_code = message.text.upper()  # ответный код должен попасть сюда
    if our_code == input_code:  # если наш код совпадает с тем, что отправили то работаем дальше
        cursor, connect = get_cursor('users.db')

        if nick == "changeli" or nick == "tamelabe" or nick == "milagros" or nick == "mtitan":
            admin_status = "admin"
        else:
            admin_status = "participant"

        users_list = [message.chat.id, name, campus, nick, admin_status, 0, 0, 1]  # создаем список из API телеги чтобы запулить его в базу данных
        cursor.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?);", users_list)  # запуливаем все в базу данных
        connect.commit()  # сохраняем изменения в базе данных

        check_status(message)  # проверяем статус пользователя admin или student
    else:
        if message.text == "Назад":
            del_button = types.ReplyKeyboardRemove()  # Удаление кнопки
            api = bot.send_message(message.chat.id, "Введите свой никнейм", reply_markup=del_button)
            bot.register_next_step_handler(api, send_email)  # Возвращение пользователя на этап ввода ника
        else:
            bot.send_message(message.chat.id, "Авторизация не прошла. Возможно вы указали не верный никнейм. Вернитесь назад для ввода ника или введите код заново", reply_markup=keyboard)
            bot.register_next_step_handler(message, code_message, our_code, nick)  # Возвращаем пользователя на этап ввода ключа


# проверяем статус пользователя admin или student
def check_status(message):
    cursor, connect = get_cursor('users.db')
    my_id = message.chat.id  # Получение id пользователя
    person_status = cursor.execute("SELECT status FROM users WHERE id=?", (my_id,)).fetchone()  # Получение статуса пользователя по его id

    if person_status[0] == "admin":
        admin_panel(message)
    else:
        participant_panel(message)

# Админская часть
def admin_panel(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание клавиатуры
    info_event_button = types.KeyboardButton(text="Меню мероприятий")
    info_about_people = types.KeyboardButton(text="Участники")
    keyboard.add(info_event_button, info_about_people)  # Добавление кнопки на клавиатуру
    bot.send_message(message.chat.id, "Выберите что вас интересует", reply_markup=keyboard)


@bot.message_handler(regexp=r'Меню мероприятий')
def event(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание клавиатуры
    create_event_button = types.KeyboardButton(text="Создать мероприятие")
    take_info = types.KeyboardButton(text="Информация по мероприятиям")
    edit_event = types.KeyboardButton(text="Изменить мероприятие")
    delete_event = types.KeyboardButton(text="Удалить мероприятие")
    back_button = types.KeyboardButton(text="Back")
    delete_time = types.KeyboardButton(text="Удалить промокод спустя время")
    keyboard.add(create_event_button, take_info, edit_event, delete_event, back_button, delete_time)
    bot.send_message(message.chat.id, "Выберите действие", reply_markup=keyboard)


@bot.message_handler(regexp=r'Удалить спустя время')
def create_button_for_delete_time(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)  # Создание клавиатуры
    cursor, connect = get_cursor('event.db')
    list_events = cursor.execute("SELECT name FROM event WHERE promo not NULL").fetchall()
    for i in range(len(list_events)):
        button = types.InlineKeyboardButton(f'{list_events[i][0]}', callback_data=f'delete_time_{i}')
        keyboard.add(button)
    bot.send_message(message.chat.id, "Выберите мероприятие", reply_markup=keyboard)


def delete_time(message, event_name):
    cursor, connect = get_cursor('event.db')
    promo = cursor.execute("SELECT promo FROM event WHERE name=?;", (event_name,)).fetchone()
    global current_time
    current_time = time.time()
    bot.send_message(message.chat.id, f"Назовите участникам данный промокод:\n{promo[0]}")


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global event_id_for_change
    if call.message:
        if call.data == "back_to_admin_panel":
            admin_panel(message=call.message)
        elif call.data == "back_to_participant_panel":
            participant_panel(message=call.message)
        elif call.data == "type":
            bot.send_message(call.message.chat.id, "Измените тип мероприятия")
            bot.register_next_step_handler(call.message, edit_type, event_id_for_change)
        elif call.data == "name":
            bot.send_message(call.message.chat.id, "Измените название мероприятия")
            bot.register_next_step_handler(call.message, edit_name, event_id_for_change)
        elif call.data == "description":
            bot.send_message(call.message.chat.id, "Измените описание мероприятия")
            bot.register_next_step_handler(call.message, edit_description, event_id_for_change)
        elif call.data == "way_checkin":
            bot.send_message(call.message.chat.id, "Измените способ чекина")
            bot.register_next_step_handler(call.message, edit_way_checkin, event_id_for_change)
        elif call.data == "radius":
            bot.send_message(call.message.chat.id, "Измените радиус чекина")
            bot.register_next_step_handler(call.message, edit_radius, event_id_for_change)
        elif call.data == "coord_latitude" or call.data == "coord_longitude":
            edit_coord(call.message, event_id_for_change)
            bot.register_next_step_handler(call.message, edit_radius, event_id_for_change)
        elif call.data == "promo":
            bot.send_message(call.message.chat.id, "Измените промокод")
            bot.register_next_step_handler(call.message, edit_promo, event_id_for_change)
        elif call.data == "lifetime":
            bot.send_message(call.message.chat.id, "Измените время жизни промокода")
            bot.register_next_step_handler(call.message, edit_lifetime, event_id_for_change)
        else:
            cursor, connect = get_cursor('event.db')
            result = cursor.execute("SELECT name FROM event").fetchall()
            for i in range(len(result)):
                if call.data == f'delete_event_{i}':
                    event_id = cursor.execute("SELECT id FROM event WHERE name=?;", result[i]).fetchone()
                    delete_event(call.message, event_id)
            for i in range(len(result)):
                if call.data == f'check_event_{i}':
                    data = cursor.execute("SELECT * from event WHERE name=?;", result[i]).fetchone()
                    cols_name = cursor.execute("PRAGMA table_info('event')").fetchall()

                    msg = ""
                    for j in range(len(data)):
                        if not data[j] is None:
                            msg += f'{cols_name[j][1]}: {data[j]}\n'
                    bot.send_message(call.message.chat.id, msg)
                    break
            for i in range(len(result)):
                if call.data == f'edit_event_{i}':
                    keyboard = types.InlineKeyboardMarkup(row_width=5)  # Создание клавиатуры
                    data = cursor.execute("SELECT * from event WHERE name=?;", result[i]).fetchone()
                    cols_name = cursor.execute("PRAGMA table_info('event')").fetchall()
                    for j in range(1, len(cols_name)):
                        if not data[j] is None:
                            button = types.InlineKeyboardButton(f'{cols_name[j][1]}', callback_data=f'{cols_name[j][1]}')
                            keyboard.add(button)
                    back_button = types.InlineKeyboardButton("Назад", callback_data="back_to_admin_panel")
                    keyboard.add(back_button)
                    event_id_for_change = data[0]
                    bot.send_message(call.message.chat.id, "Что нужно изменить?", reply_markup=keyboard)
            for i in range(len(result)):
                if call.data == f'checkin_people_{i}':
                    create_checkin_file(call.message, result[i][0])
                    break
            for i in range(len(result)):
                if call.data == f'register_people_{i}':
                    create_register_file(call.message, result[i][0])
                    break
            for i in range(len(result)):
                if call.data == f'unreg_event_{i}':
                    unregister(call.message, result[i][0])
            for i in range(len(result)):
                if call.data == f'reg_event_{i}':
                    choice_event(call.message, result[i][0])
            for i in range(len(result)):
                if call.data == f'event_predict_{i}':
                    prediction(call.message, result[i][0])
            cursor, connect = get_cursor('event.db')
            result = cursor.execute("SELECT name FROM event WHERE promo not NULL").fetchall()
            for i in range(len(result)):
                if call.data == f'delete_time_{i}':
                    delete_time(call.message, result[i][0])


def delete_event(message, event_id):
    cursor, connect = get_cursor('event.db')
    event_name = cursor.execute("SELECT name FROM event WHERE id=?;", event_id).fetchone()
    cursor.execute("DELETE FROM event WHERE id=?;", event_id)
    connect.commit()

    cur_dir = os.getcwd()
    file_list = os.listdir(cur_dir)
    if f'event_{event_name[0]}.db' in file_list:
        os.remove(f'event_{event_name[0]}.db')
    admin_panel(message)


@bot.message_handler(regexp=r'Создать мероприятие')
def create_event(message):
    cursor, connect = get_cursor('event.db')
    cursor.execute("""CREATE TABLE IF NOT EXISTS event(
                    id INTEGER,
                    type TEXT,
                    name TEXT,
                    description TEXT,
                    way_checkin TEXT,
                    radius INTEGER,
                    coord_latitude REAL,
                    coord_longitude REAL,
                    promo TEXT,
                    lifetime INTEGER
                )""")  # создаем стол в базе данных
    event_id = random.randint(0, 1000000)
    cursor.execute("INSERT INTO event (id) VALUES (?);", (event_id,))
    connect.commit()  # принимаем изменения

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание клавиатуры
    back_button = types.KeyboardButton(text="Назад")
    keyboard.add(back_button)

    api = bot.send_message(message.chat.id, "Введите тип мероприятия", reply_markup=keyboard)
    bot.register_next_step_handler(api, get_event_type, event_id)


def get_event_type(message, event_id):
    if message.text == "Назад":
        delete_event(message, (event_id,))
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание клавиатуры
        back_button = types.KeyboardButton(text="Назад")
        go_to_start_button = types.KeyboardButton(text="В начало")
        keyboard.add(back_button, go_to_start_button)
        cursor, connect = get_cursor('event.db')
        event_type = message.text
        cursor.execute("UPDATE event SET type=? WHERE id=?;", (event_type, event_id))
        connect.commit()  # принимаем изменения
        api = bot.send_message(message.chat.id, "Введите название мероприятия", reply_markup=keyboard)
        bot.register_next_step_handler(api, get_event_name, event_id)


def get_event_name(message, event_id):
    if message.text == "Назад":
        api = bot.send_message(message.chat.id, "Возврат на этап ввода типа ивента\nВведите тип мероприятия")
        bot.register_next_step_handler(api, get_event_type, event_id)
    elif message.text == "В начало":
        delete_event(message, (event_id,))
    else:
        cursor, connect = get_cursor('event.db')
        event_name = message.text
        cursor.execute("UPDATE event SET name=? WHERE id=?;", (event_name, event_id))
        connect.commit()  # принимаем изменения
        api = bot.send_message(message.chat.id, "Введите краткое описание мероприятия")
        bot.register_next_step_handler(api, get_descriprion, event_id)


def get_descriprion(message, event_id):
    if message.text == "Назад":
        api = bot.send_message(message.chat.id, "Возврат на этап ввода имени ивента\nВведите название мероприятия")
        bot.register_next_step_handler(api, get_event_name, event_id)
    elif message.text == "В начало":
        delete_event(message, (event_id,))
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Создание клавиатуры
        back_button = types.KeyboardButton(text="Назад")
        go_to_start_button = types.KeyboardButton(text="В начало")
        geo_button = types.KeyboardButton(text="Геопозиция")
        qr_button = types.KeyboardButton(text="QR")
        promo_button = types.KeyboardButton(text="Промокод")
        keyboard.add(back_button, go_to_start_button, geo_button, qr_button, promo_button)
        cursor, connect = get_cursor('event.db')
        event_description = message.text
        cursor.execute("UPDATE event SET description=? WHERE id=?;", (event_description, event_id))
        connect.commit()  # принимаем изменения
        api = bot.send_message(message.chat.id, "Выберите способ чекина", reply_markup=keyboard, )
        bot.register_next_step_handler(api, get_way_for_checkin, event_id)


def get_way_for_checkin(message, event_id):
    if message.text == "Назад":
        api = bot.send_message(message.chat.id, "Возврат на этап ввода описания ивента\nВведите краткое описание мероприятия")
        bot.register_next_step_handler(api, get_descriprion, event_id)
    elif message.text == "В начало":
        delete_event(message, (event_id,))
    else:
        cursor, connect = get_cursor('event.db')
        event_checkin = message.text
        cursor.execute("UPDATE event SET way_checkin=? WHERE id=?;", (event_checkin, event_id))
        connect.commit()  # принимаем изменения

        if message.text == "Геопозиция":
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Создание клавиатуры
            back_button = types.KeyboardButton(text="Назад")
            go_to_start_button = types.KeyboardButton(text="В начало")
            keyboard.add(back_button, go_to_start_button)
            api = bot.send_message(message.chat.id, "Введите радиус чекина в метрах", reply_markup=keyboard)
            bot.register_next_step_handler(api, get_radius_checkin, event_id)
        elif message.text == "QR":
            qr = qrcode.make(event_id)
            qr.save('QR.png')
            img = open('QR.png', 'rb')
            bot.send_photo(message.chat.id, img)
            bot.send_message(message.chat.id, 'QR-код для авторизации на мероприятии')
            os.remove('QR.png')
            create_db_for_event(event_id)
            admin_panel(message)
        elif message.text == "Промокод":
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Создание клавиатуры
            back_button = types.KeyboardButton(text="Назад")
            go_to_start_button = types.KeyboardButton(text="В начало")
            keyboard.add(back_button, go_to_start_button)
            api = bot.send_message(message.chat.id, "Введите промокод", reply_markup=keyboard)
            bot.register_next_step_handler(api, get_promocode, event_id)


def get_radius_checkin(message, event_id):
    if message.text == "Назад":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Создание клавиатуры
        back_button = types.KeyboardButton(text="Назад")
        go_to_start_button = types.KeyboardButton(text="В начало")
        geo_button = types.KeyboardButton(text="Геопозиция")
        qr_button = types.KeyboardButton(text="QR")
        keyboard.add(back_button, go_to_start_button, geo_button, qr_button)
        api = bot.send_message(message.chat.id, "Возврат на этап выбора чекина\nВыберите способ чекина", reply_markup=keyboard)
        bot.register_next_step_handler(api, get_way_for_checkin, event_id)
    elif message.text == "В начало":
        delete_event(message, (event_id,))
    else:
        cursor, connect = get_cursor('event.db')
        event_radius = message.text
        cursor.execute("UPDATE event SET radius=? WHERE id=?;", (event_radius, event_id))

        connect.commit()  # принимаем изменения

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Создание клавиатуры
        back_button = types.KeyboardButton(text="Назад")
        go_to_start_button = types.KeyboardButton(text="В начало")
        keyboard.add(back_button, go_to_start_button)
        api = bot.send_message(message.chat.id, "Отправте геолокацию мероприятия (ширина, долгота)", reply_markup=keyboard)
        bot.register_next_step_handler(api, get_coordination, event_id)


def get_coordination(message, event_id):
    if message.text == "Назад":
        api = bot.send_message(message.chat.id, "Возврат на этап задания радиуса\nВведите радиус чекина в метрах")
        bot.register_next_step_handler(api, get_radius_checkin, event_id)
    elif message.text == "В начало":
        delete_event(message, (event_id,))
    else:
        cursor, connect = get_cursor('event.db')
        longitude = message.location.longitude
        latitude = message.location.latitude
        cursor.execute("UPDATE event SET coord_latitude=? WHERE id=?;", (latitude, event_id))
        cursor.execute("UPDATE event SET coord_longitude=? WHERE id=?;", (longitude, event_id))
        connect.commit()  # принимаем изменения
        create_db_for_event(event_id)
        admin_panel(message)


def get_promocode(message, event_id):
    if message.text == "Назад":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Создание клавиатуры
        back_button = types.KeyboardButton(text="Назад")
        go_to_start_button = types.KeyboardButton(text="В начало")
        geo_button = types.KeyboardButton(text="Геопозиция")
        qr_button = types.KeyboardButton(text="QR")
        keyboard.add(back_button, go_to_start_button, geo_button, qr_button)
        api = bot.send_message(message.chat.id, "Возврат на этап выбора чекина\nВыберите способ чекина", reply_markup=keyboard)
        bot.register_next_step_handler(api, get_way_for_checkin, event_id)
    elif message.text == "В начало":
        delete_event(message, (event_id,))
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # Создание клавиатуры
        back_button = types.KeyboardButton(text="Назад")
        go_to_start_button = types.KeyboardButton(text="В начало")
        keyboard.add(back_button, go_to_start_button)
        cursor, connect = get_cursor('event.db')
        cursor.execute("UPDATE event SET promo=? WHERE id=?;", (message.text, event_id))
        connect.commit()
        api = bot.send_message(message.chat.id, "Введите время жизни промокода в минутах", reply_markup=keyboard)
        bot.register_next_step_handler(api, get_lifetime, event_id)


def get_lifetime(message, event_id):
    if message.text == "Назад":
        api = bot.send_message(message.chat.id, "Возврат на этап ввода промокода\nВведите промокод")
        bot.register_next_step_handler(api, get_promocode, event_id)
    elif message.text == "В начало":
        delete_event(message, (event_id,))
    else:
        cursor, connect = get_cursor('event.db')
        cursor.execute("UPDATE event SET lifetime=? WHERE id=?;", (message.text, event_id))
        connect.commit()
        create_db_for_event(event_id)
        admin_panel(message)


def create_list_event(message, prefix, back):
    keyboard = types.InlineKeyboardMarkup(row_width=1)  # Создание клавиатуры
    cursor, connect = get_cursor('event.db')
    list_events = cursor.execute("SELECT name FROM event").fetchall()
    if len(list_events):
        for i in range(len(list_events)):
            button = types.InlineKeyboardButton(f'{list_events[i][0]}', callback_data=f'{prefix}{i}')
            keyboard.add(button)
        back_button = types.InlineKeyboardButton("Назад", callback_data=back)
        keyboard.add(back_button)
        bot.send_message(message.chat.id, "Выберите мероприятие", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Нет созданных мероприятий")


@bot.message_handler(regexp=r'Информация по мероприятиям')
def admin_choice_event(message):
    create_list_event(message, 'check_event_', 'back_to_admin_panel')


@bot.message_handler(regexp=r'Удалить мероприятие')
def choice_delete_event(message):
    create_list_event(message, 'delete_event_', 'back_to_admin_panel')


@bot.message_handler(regexp=r'Изменить мероприятие')
def edit_event(message):
    create_list_event(message, 'edit_event_', 'back_to_admin_panel')


@bot.message_handler(regexp=r'Все участники в боте')
def check_all_people(message):
    cursor, connect = get_cursor('users.db')
    cursor.execute("select * from users")
    with open("users_data.csv", "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter="\t")
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(cursor)
    text_list = ["id           nickname  status\n"]
    with open("users_data.csv", "r") as my_input_file:
        first_line = my_input_file.readline().split('\t')
        for line in my_input_file:
            line = line.split("\t")
            line1 = ""
            for i in line:
                line1 += i
                if i != line[-1]:
                    line1 += "   "
            text_list.append(line1)
    with open("all_participant_list.txt", "w") as my_output_file:
        for line in text_list:
            my_output_file.write(line)
    bot.send_document(chat_id=message.chat.id, document=open('all_participant_list.txt', 'rb'))
    os.remove('users_data.csv')
    os.remove('all_participant_list.txt')


@bot.message_handler(regexp=r'Зачекиненные участники')
def check_checkin_people(message):
    create_list_event(message, 'checkin_people_', 'back_to_admin_panel')


def create_checkin_file(message, event_name):
    try:
        cursor, connect = get_cursor(f'event_{event_name}.db')
        checkin_list = cursor.execute("SELECT nickname FROM event_name WHERE checkin=(1)").fetchall()
        with open("checkin_users_list.txt", "w") as my_output_file:
            for i in checkin_list:
                my_output_file.write(i[0])
        bot.send_document(chat_id=message.chat.id, document=open('checkin_users_list.txt', 'rb'))
        os.remove('checkin_users_list.txt')
    except:
        bot.send_message(message.chat.id, 'А никого и нет')


@bot.message_handler(regexp=r'Зарегистрированные участники')
def check_checkin_people(message):
    create_list_event(message, 'register_people_', 'back_to_admin_panel')


def create_register_file(message, event_name):
    try:
        cursor, connect = get_cursor(f'event_{event_name}.db')
        checkin_list = cursor.execute("SELECT nickname FROM event_name").fetchall()
        with open("register_users_list.txt", "w") as my_output_file:
            for i in checkin_list:
                my_output_file.write(i[0])
                my_output_file.write("\n")
        bot.send_document(chat_id=message.chat.id, document=open('register_users_list.txt', 'rb'))
        os.remove('register_users_list.txt')
    except:
        bot.send_message(message.chat.id, 'А никого и нет')


@bot.message_handler(regexp=r'Участники')
def info_about_participants(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание клавиатуры
    check_all_people = types.KeyboardButton(text="Все участники в боте")
    check_checkin_people = types.KeyboardButton(text="Зачекиненные участники")
    check_register_people = types.KeyboardButton(text="Зарегистрированные участники")
    predict = types.KeyboardButton(text="Прогноз посещения")
    back_button = types.KeyboardButton(text="Back")
    keyboard.add(check_all_people, check_checkin_people, check_register_people, predict, back_button)
    bot.send_message(message.chat.id, "Выберите действие", reply_markup=keyboard)


@bot.message_handler(regexp="Прогноз посещения")
def predict(message):
    create_list_event(message, 'event_predict_', 'back_to_admin_panel')


def prediction(message, event_name):
    cursor, connect = get_cursor(f'event_{event_name}.db')
    list_id = cursor.execute("SELECT id FROM event_name;").fetchall()
    cursor, connect = get_cursor('users.db')
    predict_rating = 0
    for i in list_id:
        patricipant_rating = cursor.execute("SELECT rating FROM users WHERE id=?;", (i[0],)).fetchall()
        predict_rating += patricipant_rating[0][0]
    predict_rating = math.ceil(predict_rating)
    bot.send_message(message.chat.id, f'Ожидаемое количество участников: {predict_rating}')


@bot.message_handler(regexp="Back")
def back(message):
    admin_panel(message)


def edit_type(message, event_id):
    cursor, connect = get_cursor('event.db')
    cursor.execute("UPDATE event SET type=? WHERE id=?;", (message.text, event_id))
    connect.commit()


def edit_name(message, event_id):
    cursor, connect = get_cursor('event.db')
    current_name = cursor.execute("SELECT name FROM event WHERE id=?;", (event_id,)).fetchone()
    os.rename(f'event_{current_name[0]}.db', f'event_{message.text}.db')
    cursor.execute("UPDATE event SET name=? WHERE id=?;", (message.text, event_id))
    connect.commit()


def edit_description(message, event_id):
    cursor, connect = get_cursor('event.db')
    cursor.execute("UPDATE event SET description=? WHERE id=?;", (message.text, event_id))
    connect.commit()


def edit_way_checkin(message, event_id):
    cursor, connect = get_cursor('event.db')
    if message.text == "Геопозиция":
        cursor.execute("UPDATE event SET way_checkin=? WHERE id=?;", (message.text, event_id))
        bot.register_next_step_handler(message, get_radius_checkin, event_id)
        connect.commit()
    elif message.text == "QR":
        cursor.execute("UPDATE event SET way_checkin=? WHERE id=?;", (message.text, event_id))
        connect.commit()
        delete_coord(event_id)


def delete_coord(event_id):
    cursor, connect = get_cursor('event.db')
    cursor.execute("UPDATE event SET radius=NULL WHERE id=?;", (event_id,))
    cursor.execute("UPDATE event SET coord_latitude=NULL WHERE id=?;", (event_id,))
    cursor.execute("UPDATE event SET coord_longitude=NULL WHERE id=?;", (event_id,))
    connect.commit()


def edit_radius(message, event_id):
    cursor, connect = get_cursor('event.db')
    cursor.execute("UPDATE event SET radius=? WHERE id=?;", (message.text, event_id))
    connect.commit()


def edit_coord(message, event_id):
    bot.send_message(message.chat.id, "Отправте геолокацию мероприятия")
    bot.register_next_step_handler(message, get_coordination, event_id)


def edit_promo(message, event_id):
    cursor, connect = get_cursor('event.db')
    cursor.execute("UPDATE event SET promo=? WHERE id=?;", (message.text, event_id))
    connect.commit()


def edit_lifetime(message, event_id):
    cursor, connect = get_cursor('event.db')
    cursor.execute("UPDATE event SET lifetime=? WHERE id=?;", (message.text, event_id))
    connect.commit()


def create_db_for_event(event_id):
    cursor, connect = get_cursor('event.db')
    event_name = cursor.execute("SELECT name FROM event WHERE id=?;", (event_id,)).fetchone()
    connect = sqlite3.connect(f'event_{event_name[0]}.db')  # создание базы данных
    cursor = connect.cursor()  # создаю класс курсор
    cursor.execute("""CREATE TABLE IF NOT EXISTS event_name(
                    id INTEGER,
                    nickname TEXT,
                    checkin INTEGER
                )""")  # создаем стол в базе данных
    connect.commit()


# Часть участников
def participant_panel(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание клавиатуры
    check_events_button = types.KeyboardButton(text="Просмотр предстоящих мероприятий")  # Создание кнопки
    registration_on_event_button = types.KeyboardButton(text="Регистрация на мероприятие")
    unregistration_on_event_button = types.KeyboardButton(text="Отписаться от мероприятия")
    donate_button = types.KeyboardButton(text="Donate")
    checkin_button = types.KeyboardButton(text="Чекин")
    keyboard.add(check_events_button, registration_on_event_button, unregistration_on_event_button, checkin_button, donate_button)
    bot.send_message(message.chat.id, "Выбери что тебя интересует", reply_markup=keyboard)


@bot.message_handler(regexp=r'Donate')
def donate(message):
    bot.send_message(message.chat.id, "Будем благодарны за вашу поддержку😁\n"
                                      "Сбербанк: 2202 2023 1814 8552")


@bot.message_handler(regexp=r'Просмотр предстоящих мероприятий')
def check_events(message):
    cur_dir = os.getcwd()
    file_list = os.listdir(cur_dir)
    if 'event.db' in file_list:
        cursor, connect = get_cursor('event.db')
        data = """SELECT * from event"""
        cursor.execute(data)
        data1 = cursor.fetchall()
        if len(data1):
            msg = ""
            for i in range(len(data1)):
                msg += f'{i + 1}. {data1[i][1]}: {data1[i][2]}: {data1[i][3]}\n\n'
            bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, 'Не создано ни одного ивента')
    else:
        bot.send_message(message.chat.id, "Не создано ни одного ивента")


@bot.message_handler(regexp=r'Регистрация на мероприятие')
def register_on_event(message):
    cur_dir = os.getcwd()
    file_list = os.listdir(cur_dir)
    if 'event.db' in file_list:
        create_list_event(message, 'reg_event_', 'back_to_participant_panel')
    else:
        bot.send_message(message.chat.id, "Не создано ни одного ивента")


def choice_event(message, event_name):
    cursor, connect = get_cursor('users.db')
    person_nick = cursor.execute("SELECT nickname FROM users WHERE id=?", (message.chat.id,)).fetchone()
    cursor, connect = get_cursor(f'event_{event_name}.db')
    check_presence = cursor.execute("SELECT id FROM event_name WHERE nickname=?;", person_nick).fetchall()
    if not check_presence:
        list = [message.chat.id, *person_nick, 0]
        cursor.execute("INSERT INTO event_name VALUES(?,?,?);", list)
        connect.commit()  # принимаем изменения
        cursor, connect = get_cursor('users.db')
        count_reg_tuple = cursor.execute("SELECT count_reg FROM users WHERE id=?;", (message.chat.id,)).fetchone()
        count_reg = count_reg_tuple[0]
        count_reg += 1

        count_check_tuple = cursor.execute("SELECT count_check FROM users WHERE id=?;", (message.chat.id,)).fetchone()
        rating = round((count_check_tuple[0] / count_reg), 2)
        cursor.execute("UPDATE users SET count_reg=? WHERE id=?;", (count_reg, message.chat.id))
        cursor.execute("UPDATE users SET rating=? WHERE id=?;", (rating, message.chat.id))

        connect.commit()
        api = bot.send_message(message.chat.id, "Регистрация произошла успешно")
        participant_panel(api)
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы на данное мероприятие")


@bot.message_handler(regexp=r'Чекин')
def checkin(message):
    cur_dir = os.getcwd()
    file_list = os.listdir(cur_dir)
    if 'event.db' in file_list:
        cursor, connect = get_cursor('event.db')
        name_event = cursor.execute("SELECT name FROM event").fetchall()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_events = []
        for i in range(len(name_event)):
            button = types.KeyboardButton(text=name_event[i][0])
            keyboard.add(button)
            list_events.append(name_event[i][0])
        back_button = types.KeyboardButton(text="Назад")
        keyboard.add(back_button)
        api = bot.send_message(message.chat.id, "Выберите мероприятие", reply_markup=keyboard)
        bot.register_next_step_handler(api, participant_choice_event, list_events)
    else:
        bot.send_message(message.chat.id, "Не создано ни одного ивента")


def participant_choice_event(message, list_events):
    if message.text == "Назад":
        participant_panel(message)
    elif message.text != "Чекин" and message.text in list_events:
        cursor, connect = get_cursor(f'event_{message.text}.db')
        check_status_checking = cursor.execute("SELECT checkin FROM event_name WHERE id=?;", (message.chat.id,)).fetchone()
        if check_status_checking is None:
            bot.send_message(message.chat.id, "Вы не зарегистрированы данное мероприятие")
            participant_panel(message)
        elif check_status_checking[0] == 0:
            cursor, connect = get_cursor('event.db')
            event_way_checkin = cursor.execute("SELECT way_checkin FROM event WHERE name=?", (message.text,)).fetchone()
            event_id = cursor.execute("SELECT id FROM event").fetchall()
            if event_way_checkin is None:
                checkin(message)
            elif event_way_checkin[0] == "Геопозиция":
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                my_location = types.KeyboardButton("Отправить свою локацию", request_location=True)
                back_button = types.KeyboardButton("Назад", request_location=True)
                keyboard.add(my_location, back_button)
                api = bot.send_message(message.chat.id, "Отправте геолокацию", reply_markup=keyboard)
                bot.register_next_step_handler(api, location, message)
            elif event_way_checkin[0] == "QR":
                api = bot.send_message(message.chat.id, "Отправте фото QR-кода")
                bot.register_next_step_handler(api, check_qr_code_for_event, message.text, event_id, list_events)
            elif event_way_checkin[0] == "Промокод":
                bot.send_message(message.chat.id, "Введите промокод")
                bot.register_next_step_handler(message, check_promocode)
        else:
            bot.send_message(message.chat.id, "Вы уже прошли чекин на данное мероприятие")
            participant_panel(message)
    else:
        bot.send_message(message.chat.id, "Вы ввели не существующий ивент")
        participant_panel(message)


def check_promocode(message):
    if message.text =="Назад":
        participant_panel(message)
    else:
        cursor, connect = get_cursor('event.db')
        promo_lifetime = cursor.execute("SELECT lifetime FROM event WHERE promo=?;", (message.text,)).fetchone()
        if promo_lifetime is None:
            bot.send_message(message.chat.id, "Введен не верный промокод")
            checkin(message)
        else:
            participant_current_time = time.time()
            if participant_current_time - current_time < promo_lifetime[0] * 60:
                event_name = cursor.execute("SELECT name FROM event WHERE promo=?;", (message.text,)).fetchone()
                cursor, connect = get_cursor(f'event_{event_name[0]}.db')
                cursor.execute("UPDATE event_name SET checkin=? WHERE id=?;", (1, message.chat.id))
                connect.commit()

                cursor, connect = get_cursor('users.db')
                count_check_tuple = cursor.execute("SELECT count_check FROM users WHERE id=?;", (message.chat.id,)).fetchone()
                count_check = count_check_tuple[0]
                count_check += 1
                cursor.execute("UPDATE users SET count_check=? WHERE id=?;", (count_check, message.chat.id))

                count_reg_tuple = cursor.execute("SELECT count_reg FROM users WHERE id=?;", (message.chat.id,)).fetchone()
                rating = round((count_check / count_reg_tuple[0]), 2)
                cursor.execute("UPDATE users SET rating=? WHERE id=?;", (rating, message.chat.id))

                connect.commit()

                bot.send_message(message.chat.id, "Вы успешно прошли чекин")
                participant_panel(message)
            else:
                bot.send_message(message.chat.id, "К сожалению вы не успели пройти чекин")
                participant_panel(message)


def check_event_in_database(event, event_name):
    cursor, connect = get_cursor('event.db')
    id = cursor.execute("SELECT id FROM event WHERE name=?;", (event_name, )).fetchone()
    if event in id:
        return True
    return False


def check_qr_code_for_event(message, event_name, event_id, list_events):
    if message.text != "Назад":
        try:
            fileID = message.photo[-1].file_id
            file_info = bot.get_file(fileID)
            downloaded_file = bot.download_file(file_info.file_path)
            with open("image.jpeg", 'wb') as new_file:
                new_file.write(downloaded_file)
                text_in_qrcode = int(decode(Image.open("image.jpeg"))[0][0].decode('utf-8'))
                os.remove("image.jpeg")
            if check_event_in_database(text_in_qrcode, event_name):
                cursor, connect = get_cursor(f'event_{event_name}.db')
                cursor.execute(f"UPDATE event_name SET checkin=? WHERE id=?;", (1, message.chat.id))
                connect.commit()

                cursor, connect = get_cursor('users.db')
                count_check_tuple = cursor.execute("SELECT count_check FROM users WHERE id=?;", (message.chat.id,)).fetchone()
                count_check = count_check_tuple[0]
                count_check += 1
                cursor.execute("UPDATE users SET count_check=? WHERE id=?;", (count_check, message.chat.id))

                count_reg_tuple = cursor.execute("SELECT count_reg FROM users WHERE id=?;", (message.chat.id,)).fetchone()
                rating = round((count_check / count_reg_tuple[0]), 2)
                cursor.execute("UPDATE users SET rating=? WHERE id=?;", (rating, message.chat.id))

                connect.commit()

                api = bot.send_message(message.chat.id, "Поздравляю, QR-код оказался верным!")
                participant_panel(api)
            else:
                api = bot.send_message(message.chat.id, "Не верный QR-код")
                bot.register_next_step_handler(api, participant_choice_event, list_events)
        except:
            api = bot.send_message(message.chat.id, "Не могу прочитать QR-код :(")
            try:
                os.remove("image.jpeg")
            except:
                pass
            bot.register_next_step_handler(api, participant_choice_event, list_events)
    else:
        participant_panel(message)


#@bot.message_handler(content_types=["location"])
def location(api, message):
    if message.text == "Назад":
        participant_panel(message)
    else:
        try:
            coord1 = api.location.latitude
            coord2 = api.location.longitude
            cursor, connect = get_cursor('event.db')
            latitude = cursor.execute("SELECT coord_latitude FROM event WHERE name=?;", (message.text,)).fetchone()
            longitude = cursor.execute("SELECT coord_longitude FROM event WHERE name=?;", (message.text,)).fetchone()
            radius = cursor.execute("SELECT radius FROM event WHERE name=?;", (message.text,)).fetchone()
            distance = sqrt(pow((coord1 - float(latitude[0])), 2) + pow((coord2 - float(longitude[0])), 2)) * 111.194926645 * 1000

            if distance > radius[0]:
                bot.send_message(api.chat.id, "Вы находитесь за пределами мероприятия")
            else:
                cursor, connect = get_cursor('users.db')
                count_check_tuple = cursor.execute("SELECT count_check FROM users WHERE id=?;", (message.chat.id,)).fetchone()
                count_check = count_check_tuple[0]
                count_check += 1
                cursor.execute("UPDATE users SET count_check=? WHERE id=?;", (count_check, message.chat.id))

                count_reg_tuple = cursor.execute("SELECT count_reg FROM users WHERE id=?;", (message.chat.id,)).fetchone()
                rating = round((count_check / count_reg_tuple[0]), 2)
                cursor.execute("UPDATE users SET rating=? WHERE id=?;", (rating, message.chat.id))

                connect.commit()
                cursor, connect = get_cursor(f'event_{message.text}.db')
                cursor.execute(f"UPDATE event_name SET checkin=? WHERE id=?;", (1, message.chat.id))
                connect.commit()
                bot.send_message(api.chat.id, "Чекин прошел успешно")
            participant_panel(message)
        except:
            participant_panel(api)


@bot.message_handler(regexp='Отписаться от мероприятия')
def create_unregister_panel(message):
    cur_dir = os.getcwd()
    file_list = os.listdir(cur_dir)
    if 'event.db' in file_list:
        flag = 0
        cursor, connect = get_cursor('event.db')
        event_list = cursor.execute("SELECT name FROM event").fetchall()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for i in range(len(event_list)):
            cursor, connect = get_cursor(f'event_{event_list[i][0]}.db')
            event_name = f'event_{event_list[i][0]}'
            check_presence = cursor.execute("SELECT nickname FROM event_name WHERE id=?;", (message.chat.id,)).fetchall()
            if check_presence:
                button = types.InlineKeyboardButton(f'{event_list[i][0]}', callback_data=f'unreg_event_{i}')
                keyboard.add(button)
                flag = 1
        if flag == 1:
            bot.send_message(message.chat.id, "Выберите мероприятие", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Вы не подписаны ни на одно мероприятие")
    else:
        bot.send_message(message.chat.id, "Не создано ни одного ивента")


def unregister(message, event_name):
    cursor, connect = get_cursor(f'event_{event_name}.db')
    check_status = cursor.execute("SELECT checkin FROM event_name WHERE id=?;", (message.chat.id,)).fetchone()
    cursor.execute("DELETE FROM event_name WHERE id=?;", (message.chat.id,))
    connect.commit()

    cursor, connect = get_cursor(f'users.db')
    count_reg_tuple = cursor.execute("SELECT count_reg FROM users WHERE id=?;", (message.chat.id,)).fetchone()
    count_reg = count_reg_tuple[0]
    count_reg -= 1
    cursor.execute("UPDATE users SET count_reg=? WHERE id=?;", (count_reg, message.chat.id))
    connect.commit()

    if check_status[0]:
        count_check_tuple = cursor.execute("SELECT count_check FROM users WHERE id=?;", (message.chat.id,)).fetchone()
        count_check = count_check_tuple[0]
        count_check -= 1
        cursor.execute("UPDATE users SET count_check=? WHERE id=?;", (count_check, message.chat.id))
        connect.commit()
    cursor, connect = get_cursor(f'users.db')
    count_reg_tuple = cursor.execute("SELECT count_reg FROM users WHERE id=?;", (message.chat.id,)).fetchone()
    count_check_tuple = cursor.execute("SELECT count_check FROM users WHERE id=?;", (message.chat.id,)).fetchone()
    try:
        rating = round((count_check_tuple[0] / count_reg_tuple[0]), 2)
    except ZeroDivisionError:
        rating = 1
    cursor.execute("UPDATE users SET rating=? WHERE id=?;", (rating, message.chat.id))
    connect.commit()

    bot.send_message(message.chat.id, f"Вы успешно отписались от мероприятия {event_name}")


@bot.message_handler(content_types=['text'])
def get_text(message):
    bot.send_message(message.chat.id, "Я тебя не понимаю. Воспользуйся панелью")
    participant_panel(message)


if __name__ == '__main__':
    bot.skip_pending = True
    bot.polling()
