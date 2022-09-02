def check_status(message):
    cursor, connect = get_cursor('users.db')
    my_id = message.chat.id  # Получение id пользователя
    person_status = cursor.execute("SELECT status FROM users WHERE id=?", (my_id,)).fetchone()  # Получение статуса пользователя по его id

    if person_status[0] == "admin":
        admin_panel(message)
    else:
        participant_panel(message)

def create_button_for_delete_time(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)  # Создание клавиатуры
    cursor, connect = get_cursor('event.db')
    list_events = cursor.execute("SELECT name FROM event WHERE promo not NULL").fetchall()
    for i in range(len(list_events)):
        button = types.InlineKeyboardButton(f'{list_events[i][0]}', callback_data=f'delete_time_{i}')
        keyboard.add(button)
    bot.send_message(message.chat.id, "Выберите мероприятие", reply_markup=keyboard)

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


def prediction(message, event_name):
    cursor, connect = get_cursor(f'event_{event_name}.db')
    list_id = cursor.execute("SELECT id FROM event_name;").fetchall()
    cursor, connect = get_cursor('users.db')
    predict_rating = 0
    for i in list_id:
        patricipant_rating = cursor.execute("SELECT rating FROM users WHERE id=?;", (i[0],)).fetchall()
        predict_rating += patricipant_rating[0][0]
    predict_rating = math.ceil(predict_rating)
    bot.send_message(message.chat.id, f'Ожидаемое количество участников {predict_rating}')

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