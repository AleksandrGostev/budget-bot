import sqlite3
import datetime
import calendar


class PaymentType:
    EXPENSE = 'expense'
    INCOME = 'income'


def insert_payment(chat_id, username, payment_type, title, price, date, category_id):
    conn = sqlite3.connect('db_budget.db')
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO payments('chat_id', 'username', 'title', 'price', 'date', 'category_id') 
            VALUES ( ?, ?, ?, ?, ?, ? )""",
        (chat_id, username, title, price, date, category_id))
    conn.commit()
    return cursor.lastrowid


def insert_category(chat_id, payment_type, title, date, position):
    conn = sqlite3.connect('db_budget.db')
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO categories ("chat_id", "payment_type", "title", "date", "position")
                    VALUES ( ?, ?, ?, ?, ? )""", (chat_id, payment_type, title, date, position))
    conn.commit()


def get_categories(chat_id, payment_type):
    conn = sqlite3.connect('db_budget.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE chat_id = ? and payment_type = ?", (chat_id, payment_type))
    conn.commit()
    return cursor.fetchall()


def get_category(chat_id, category_id):
    conn = sqlite3.connect('db_budget.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE chat_id = ? and category_id = ?", (chat_id, category_id))
    conn.commit()
    return cursor.fetchone()


def rename_category(chat_id, category_id, title):
    conn = sqlite3.connect('db_budget.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET title = ? WHERE chat_id = ? and category_id = ?",
                   (title, chat_id, category_id))
    conn.commit()


def delete_category(chat_id, category_id):
    conn = sqlite3.connect('db_budget.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payments WHERE chat_id = ? and category_id = ? ", (chat_id, category_id))
    cursor.execute("DELETE FROM categories WHERE chat_id = ? and category_id = ?", (chat_id, category_id))
    conn.commit()


def delete_payment(chat_id, payment_id):
    conn = sqlite3.connect('db_budget.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payments WHERE chat_id = ? and payment_id = ? ", (chat_id, payment_id))
    conn.commit()


def get_category_payments_current_month(chat_id, category_id):
    conn = sqlite3.connect('db_budget.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # first_day_of_month = datetime.datetime.today().replace(day=1)
    month_range = calendar.monthrange(datetime.date.year, datetime.date.month)
    first_day_of_month = month_range[0]
    last_day_of_month = month_range[1]
    cursor.execute("""SELECT c.*, sum(p.price) as amount
                        FROM categories as c
                        LEFT JOIN payments as p on p.category_id = c.category_id
                        WHERE c.chat_id = ? and date >= ? and c.date <= ?
                        group by c.category_id""",
                   (chat_id, first_day_of_month, last_day_of_month))
    conn.commit()
    return cursor.fetchall()


def get_chat_payments_current_month(chat_id, first_day_of_month, last_day_of_month):
    conn = sqlite3.connect('db_budget.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""SELECT c.*, IFNULL(SUM(p.price), 0) amount
                            FROM categories as c
                            LEFT JOIN payments as p on p.category_id = c.category_id 
                                AND c.chat_id = ? and p.date >= ? and p.date <= ?
                            group by c.category_id""",
                   (chat_id, first_day_of_month, last_day_of_month))
    return cursor.fetchall()
