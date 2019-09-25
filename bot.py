import telebot
from telebot import types
import datetime
import db_service
from db_service import PaymentType
import calendar
import os

TOKEN = os.environ.get("TOKEN", None)


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


class MessageHandler:
    insert_expense_category = False
    insert_income_category = False
    rename_category = False
    category_id = None
    price = None
    title = None


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

    for category_row in category_rows:
        cat = dict(category_row)
        if cat['payment_type'] == 'expense':
            expense_str += "{}: {} €\n".format(cat['title'], cat['amount'])
        else:
            incomes_str += "{}: {} €\n".format(cat['title'], cat['amount'])

    full_msg = "Report for {} - {}:\n\nIncomes:\n{}\nExpenses:\n{}".format(first_day_of_month, last_day_of_month,
                                                                           incomes_str, expense_str)

    bot.send_message(message.chat.id, full_msg)


@bot.message_handler(commands=['setup'])
def setup(message):
    # markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
    markup = main_menu()
    bot.send_message(message.chat.id, "Чё хочешь хозяин?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'expense' or call.data == 'income')
def categories_menu(callback):
    markup = types.InlineKeyboardMarkup(row_width=1)
    # get list of categories
    rows = db_service.get_categories(callback.message.chat.id, callback.data)
    for row in rows:
        cat = dict(row)
        markup.add(
            types.InlineKeyboardButton(cat['title'], callback_data="category_edit_{}".format(cat['category_id'])))
    add_category_btn = types.InlineKeyboardButton("Add new category",
                                                  callback_data='add_category_{}'.format(callback.data))

    back_category_btn = types.InlineKeyboardButton("Back", callback_data='back_to_main_menu')
    markup.add(add_category_btn, back_category_btn)
    bot.edit_message_text("Please select category",
                          callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('add_category'))
def add_category(callback):
    callback_data_arr = callback.data.split('_')
    category = callback_data_arr[len(callback_data_arr) - 1]
    bot.send_message(callback.message.chat.id, "Please write down category to add it to {}".format(category))
    if category == "expense":
        MessageHandler.insert_expense_category = True
    if category == "income":
        MessageHandler.insert_income_category = True


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
    category_row = db_service.get_category(callback.message.chat.id, category_id)
    category = dict(category_row)
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(types.InlineKeyboardButton("Rename", callback_data='rename_category_{}'.format(category_id)),
               types.InlineKeyboardButton("Delete", callback_data='delete_category_{}'.format(category_id)))
    markup.add(types.InlineKeyboardButton("Back", callback_data=category['payment_type']))

    bot.edit_message_text("Soon here will be sum for this category:\n {}".format(category['title']),
                          callback.message.chat.id, callback.message.message_id)
    bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('rename_category'))
def rename_category(callback):
    category_id = callback.data.split('_')[-1]
    MessageHandler.rename_category = True
    MessageHandler.category_id = category_id
    bot.send_message(callback.message.chat.id, "Please enter category new name")


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_category'))
def delete_category(callback):
    markup = types.InlineKeyboardMarkup()
    category_id = callback.data.split('_')[-1]
    markup.add(
        types.InlineKeyboardButton("Yes", callback_data="proceed_{}".format(callback.data)),
        types.InlineKeyboardButton("No", callback_data="category_edit_{}".format(category_id))
    )
    bot.edit_message_text("Are you sure?", callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('proceed_delete_category'))
def proceed_delete_category(callback):
    category_id = callback.data.split('_')[-1]
    MessageHandler.rename_category = True
    MessageHandler.rename_category_id = category_id
    db_service.delete_category(callback.message.chat.id, MessageHandler.category_id)
    bot.send_message(callback.message.chat.id, "Category deleted")


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
    markup.add(types.InlineKeyboardButton("Back", callback_data="payment_categories_main_menu"))
    bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_payment"))
def cancel_payment(callback):
    payment_id = callback.data.split("_")[-1]
    db_service.delete_payment(callback.message.chat.id, payment_id)
    cancelled_icon = u'\U0000274C'
    bot.edit_message_text(callback.message.text + "\n {} cancelled".format(cancelled_icon), callback.message.chat.id,
                          callback.message.message_id, reply_markup=())


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_payment_"))
def add_payment(callback):
    category_id = callback.data.split("_")[-1]
    payment_type = callback.data.split("_")[-2]
    category_row = db_service.get_category(callback.message.chat.id, category_id)
    category = dict(category_row)
    payment_id = db_service.insert_payment(callback.message.chat.id, callback.message.from_user.first_name,
                                           payment_type,
                                           MessageHandler.title, MessageHandler.price, datetime.datetime.today(),
                                           category_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Cancel", callback_data="cancel_payment_{}".format(payment_id)))
    bot.edit_message_text("{} was added to {}".format(MessageHandler.price, category['title']),
                          callback.message.chat.id, callback.message.message_id, reply_markup=markup)


def generate_add_menu(markup, payment_type, chat_id):
    rows = db_service.get_categories(chat_id, payment_type)
    for row in rows:
        category = dict(row)
        markup.add(
            types.InlineKeyboardButton(
                category['title'],
                callback_data="add_payment_{}_{}".format(payment_type, category['category_id'])
            )
        )


@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    if MessageHandler.insert_expense_category:
        bot.send_message(message.chat.id, "Expense category added:\n {} ".format(message.text))
        categories_list = message.text.split('\n')
        for category in categories_list:
            db_service.insert_category(message.chat.id, PaymentType.EXPENSE, category, datetime.datetime.now(), 1)
        MessageHandler.insert_expense_category = False
        return

    if MessageHandler.insert_income_category:
        bot.send_message(message.chat.id, "Income category soon will be added: {}".format(message.text))
        db_service.insert_category(message.chat.id, PaymentType.INCOME, message.text, datetime.datetime.now(), 1)
        MessageHandler.insert_income_category = False
        return

    if MessageHandler.rename_category:
        db_service.rename_category(message.chat.id, MessageHandler.category_id, message.text)
        MessageHandler.rename_category = False
        bot.send_message(message.chat.id, "Category name is updated")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    generate_add_menu(markup, PaymentType.EXPENSE, message.chat.id)
    markup.add(types.InlineKeyboardButton("Back", callback_data="payment_categories_main_menu"))
    if "-" in message.text:
        data_arr = message.text.split('-')
        MessageHandler.price = data_arr[0]
        MessageHandler.title = data_arr[1]
        if message.from_user.id == 499892188:
            bot.send_message(message.chat.id, "Я всё мужу расскажу!!")
        else:
            bot.send_message(message.chat.id, "Красава Санёк!!")
        bot.send_message(message.chat.id, "Where add?", reply_markup=markup)
        # bot.send_message(message.chat.id, "Soon categories will be shown for:\n {} \n ${}$".format(price, desc))
    if "-" not in message.text:
        try:
            price = int(message.text)
            MessageHandler.price = price
            MessageHandler.title = ""
            if message.from_user.id == 499892188:
                bot.send_message(message.chat.id, "Я всё мужу расскажу!!")
            else:
                bot.send_message(message.chat.id, "Красава Санёк!!")
            bot.send_message(message.chat.id, "Where add?", reply_markup=markup)
            # bot.send_message(message.chat.id, "Soon categories will be shown for:\n {}".format(price))
        except ValueError:
            bot.send_sticker(message.chat.id, "CAADAgADogADNmLjBTODpXLHHo4DFgQ")


bot.polling()
