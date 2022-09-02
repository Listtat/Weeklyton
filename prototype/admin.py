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
        api = bot.send_message(message.chat.id, "Выберите способо чекина", reply_markup=keyboard, )
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


@bot.message_handler(regexp=r'Зачекиненные участники')
def check_checkin_people(message):
    create_list_event(message, 'checkin_people_', 'back_to_admin_panel')


def create_checkin_file(message, event_name):
    cursor, connect = get_cursor(f'event_{event_name}.db')
    checkin_list = cursor.execute("SELECT nickname FROM event_name WHERE checkin=(1)").fetchall()
    with open("checkin_users_list.txt", "w") as my_output_file:
        for i in checkin_list:
            my_output_file.write(i[0])
    bot.send_document(chat_id=message.chat.id, document=open('checkin_users_list.txt', 'rb'))


@bot.message_handler(regexp=r'Зарегистрированные участники')
def check_checkin_people(message):
    create_list_event(message, 'register_people_', 'back_to_admin_panel')


def create_register_file(message, event_name):
    cursor, connect = get_cursor(f'event_{event_name}.db')
    checkin_list = cursor.execute("SELECT nickname FROM event_name").fetchall()
    with open("register_users_list.txt", "w") as my_output_file:
        for i in checkin_list:
            my_output_file.write(i[0])
            my_output_file.write("\n")
    bot.send_document(chat_id=message.chat.id, document=open('register_users_list.txt', 'rb'))


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
    bot.send_message(message.chat.id, f'Ожидаемое количество участников {predict_rating}')


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