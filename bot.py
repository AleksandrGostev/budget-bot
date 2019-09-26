import telebot
from telebot import types
import datetime
import db_service
from db_service import PaymentType
import calendar
import os
from flask import Flask, request

TOKEN = os.environ.get('TOKEN')
server = Flask(__name__)


# only used for console output now
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener)  # register listener

chart_with_upwards_trend = u'\U0001F4C8'
chart_with_downwards_trend = u'\U0001F4C9'

db_service = db_service.BotDB()


class MessageHandler:
    insert_category = False
    rename_category = False
    category_id = None
    price = None
    title = None
    category_type = None


def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)

    expenses_btn = types.InlineKeyboardButton(chart_with_downwards_trend + " Расходы", callback_data='expense')
    income_btn = types.InlineKeyboardButton(chart_with_upwards_trend + " Доходы", callback_data='income')
    markup.add(expenses_btn, income_btn)
    return markup


@bot.message_handler(commands=['report'])
def show_report(message):
    today = datetime.datetime.today()
    month_range = calendar.monthrange(today.year, today.month)
    first_day_of_month = today.replace(day=1).date()
    last_day_of_month = today.replace(day=month_range[1]).date()
    category_rows = db_service.get_chat_payments_current_month(message.chat.id, first_day_of_month, last_day_of_month)
    incomes_str = ""
    expense_str = ""
    total_expense = 0
    total_income = 0

    for cat in category_rows:
        title = cat[3]
        amount = cat[6]
        payment_type = cat[2]
        if payment_type == 'expense':
            total_expense += amount
            expense_str += "{}: {} €\n".format(title, amount)
        else:
            total_income += amount
            incomes_str += "{}: {} €\n".format(title, amount)
    expense_str += "-------------------\nИтого: {} €".format(total_expense)
    incomes_str += "-------------------\nИтого: {} €".format(total_income)
    full_msg = "Отчёт по дате {} - {}:\n\nДоходы:\n{}\n\nРасходы:\n{}".format(first_day_of_month, last_day_of_month,
                                                                              incomes_str, expense_str)

    bot.send_message(message.chat.id, full_msg)


@bot.message_handler(commands=['setup'])
def setup(message):
    markup = main_menu()
    bot.send_message(message.chat.id, "Чё хочешь хозяин?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'expense' or call.data == 'income')
def categories_menu(callback):
    markup = types.InlineKeyboardMarkup(row_width=1)
    categories = db_service.get_categories(callback.message.chat.id, callback.data)
    for cat in categories:
        category_id = cat[0]
        title = cat[3]
        markup.add(
            types.InlineKeyboardButton(title, callback_data="category_edit_{}".format(category_id)))
    add_category_btn = types.InlineKeyboardButton("Добавить категорию",
                                                  callback_data='add_category_{}'.format(callback.data))

    back_category_btn = types.InlineKeyboardButton("Назад", callback_data='back_to_main_menu')
    markup.add(add_category_btn, back_category_btn)
    bot.edit_message_text("Выбери категорию",
                          callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('add_category'))
def add_category(callback):
    callback_data_arr = callback.data.split('_')
    category = callback_data_arr[len(callback_data_arr) - 1]
    bot.send_message(callback.message.chat.id, "Напиши название категории")
    MessageHandler.insert_category = True
    MessageHandler.category_type = category


@bot.callback_query_handler(func=lambda callback: callback.data == 'back_to_main_menu')
def back_to_main_menu(callback):
    markup = main_menu()
    bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет обраточка")


@bot.callback_query_handler(func=lambda call: call.data.startswith('category_edit_'))
def category_edit_menu(callback):
    category_id = callback.data.split('_')[-1]
    cat = db_service.get_category(callback.message.chat.id, category_id)
    title = cat[3]
    payment_type = cat[2]
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(types.InlineKeyboardButton("Переименовать", callback_data='rename_category_{}'.format(category_id)),
               types.InlineKeyboardButton("Удалить", callback_data='delete_category_{}'.format(category_id)))
    markup.add(types.InlineKeyboardButton("Назад", callback_data=payment_type))

    bot.edit_message_text("За текущий месяц:\n {} - 0 €".format(title),
                          callback.message.chat.id, callback.message.message_id)
    bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('rename_category'))
def rename_category(callback):
    category_id = callback.data.split('_')[-1]
    MessageHandler.rename_category = True
    MessageHandler.category_id = category_id
    bot.send_message(callback.message.chat.id, "Введи новое имя категории")


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_category'))
def delete_category(callback):
    markup = types.InlineKeyboardMarkup()
    category_id = callback.data.split('_')[-1]
    markup.add(
        types.InlineKeyboardButton("Да", callback_data="proceed_{}".format(callback.data)),
        types.InlineKeyboardButton("Нет", callback_data="category_edit_{}".format(category_id))
    )
    bot.edit_message_text("Ты уверен?", callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('proceed_delete_category'))
def proceed_delete_category(callback):
    category_id = callback.data.split('_')[-1]
    db_service.delete_category(callback.message.chat.id, category_id)
    bot.send_message(callback.message.chat.id, "Категория удалена")


@bot.callback_query_handler(func=lambda call: call.data == 'payment_categories_main_menu')
def payment_main_menu(callback):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(chart_with_downwards_trend + " Расходы", callback_data='payment_menu_expense'),
        types.InlineKeyboardButton(chart_with_upwards_trend + " Доходы", callback_data='payment_menu_income'))
    bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("payment_menu"))
def get_payment_menu(callback):
    payment_type = callback.data.split('_')[-1]
    markup = types.InlineKeyboardMarkup(row_width=2)
    generate_add_menu(markup, payment_type, callback.message.chat.id)
    markup.add(types.InlineKeyboardButton("Назад", callback_data="payment_categories_main_menu"))
    bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_payment"))
def cancel_payment(callback):
    payment_id = callback.data.split("_")[-1]
    db_service.delete_payment(callback.message.chat.id, payment_id)
    cancelled_icon = u'\U0000274C'
    bot.edit_message_text(callback.message.text + "\n {} отменено".format(cancelled_icon), callback.message.chat.id,
                          callback.message.message_id, reply_markup=())


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_payment_"))
def add_payment(callback):
    category_id = callback.data.split("_")[-1]
    payment_type = callback.data.split("_")[-2]
    cat = db_service.get_category(callback.message.chat.id, category_id)
    title = cat[3]
    payment_id = db_service.insert_payment(callback.message.chat.id, callback.message.from_user.first_name,
                                           payment_type,
                                           MessageHandler.title, MessageHandler.price, datetime.datetime.today(),
                                           category_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Отменить", callback_data="cancel_payment_{}".format(payment_id)))
    bot.edit_message_text("{} добавлено в {}".format(MessageHandler.price, title),
                          callback.message.chat.id, callback.message.message_id, reply_markup=markup)


def generate_add_menu(markup, payment_type, chat_id):
    categories = db_service.get_categories(chat_id, payment_type)
    for cat in categories:
        category_id = cat[0]
        title = cat[3]
        markup.add(
            types.InlineKeyboardButton(
                title,
                callback_data="add_payment_{}_{}".format(payment_type, category_id)
            )
        )


@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    if MessageHandler.insert_category:
        bot.send_message(message.chat.id, "Категория добавлена:\n {} ".format(message.text))
        categories_list = message.text.split('\n')
        for category in categories_list:
            db_service.insert_category(
                message.chat.id, MessageHandler.category_type, category, datetime.datetime.now())
        MessageHandler.insert_category = False
        return

    if MessageHandler.rename_category:
        db_service.rename_category(message.chat.id, MessageHandler.category_id, message.text)
        MessageHandler.rename_category = False
        bot.send_message(message.chat.id, "Имя категории обновлено")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    generate_add_menu(markup, PaymentType.EXPENSE, message.chat.id)
    markup.add(types.InlineKeyboardButton("Back", callback_data="payment_categories_main_menu"))
    if "-" in message.text:
        data_arr = message.text.split('-')
        MessageHandler.price = data_arr[0].replace(',', '.')
        MessageHandler.title = data_arr[1]
        if message.from_user.id == 499892188:
            bot.send_message(message.chat.id, "Я всё мужу расскажу!!")
        else:
            bot.send_message(message.chat.id, "Красава Санёк!!")
        bot.send_message(message.chat.id, "Куда желаете добавить?", reply_markup=markup)
    if "-" not in message.text:
        try:
            price = float(message.text.replace(',', '.'))
            MessageHandler.price = price
            MessageHandler.title = ""
            if message.from_user.id == 499892188:
                bot.send_message(message.chat.id, "Я всё мужу расскажу!!")
            else:
                bot.send_message(message.chat.id, "Красава Санёк!!")
            bot.send_message(message.chat.id, "Извольте выбрать категорию?", reply_markup=markup)
        except ValueError:
            bot.send_sticker(message.chat.id, "CAADAgADogADNmLjBTODpXLHHo4DFgQ")


@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://telegram-gos-budget.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
