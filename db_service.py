import datetime
import calendar
import psycopg2
import os


class PaymentType:
    EXPENSE = 'expense'
    INCOME = 'income'


class BotDB:
    connection = None
    cursor = None

    def __init__(self):
        self.connection = psycopg2.connect(user=os.environ.get('pg-user'),
                                           password=os.environ.get('pg-password'),
                                           host="balarama.db.elephantsql.com",
                                           port="5432",
                                           database=os.environ.get('pg-user'))
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def insert_payment(self, chat_id, username, payment_type, title, price, date, category_id):
        self.cursor.execute(
            """INSERT INTO payments(chat_id, username, title, price, date, category_id) 
                VALUES ( %s, %s, %s, %s, %s, %s )""",
            (chat_id, username, title, price, date, category_id))
        self.connection.commit()
        return self.cursor.lastrowid

    def insert_category(self, chat_id, payment_type, title, date):
        self.cursor.execute(
            """INSERT INTO categories (chat_id, payment_type, title, date, position)
                VALUES ( %s, %s, %s, %s, (SELECT COALESCE(COUNT(*)+1, 0) as category_position FROM categories WHERE chat_id = %s))""",
            (chat_id, payment_type, title, date, chat_id))
        self.connection.commit()

    def get_categories(self, chat_id, payment_type):
        self.cursor.execute("SELECT * FROM categories WHERE chat_id = %s and payment_type = %s ORDER BY position",
                            (chat_id, payment_type))
        self.connection.commit()
        return self.cursor.fetchall()

    def get_category(self, chat_id, category_id):
        self.cursor.execute("SELECT * FROM categories WHERE chat_id = %s and category_id = %s", (chat_id, category_id))
        self.connection.commit()
        return self.cursor.fetchone()

    def rename_category(self, chat_id, category_id, title):
        self.cursor.execute("UPDATE categories SET title = %s WHERE chat_id = %s and category_id = %s",
                            (title, chat_id, category_id))
        self.connection.commit()

    def delete_category(self, chat_id, category_id):
        self.cursor.execute("DELETE FROM payments WHERE chat_id = %s and category_id = %s ", (chat_id, category_id))
        self.cursor.execute("DELETE FROM categories WHERE chat_id = %s and category_id = %s", (chat_id, category_id))
        self.connection.commit()

    def delete_payment(self, chat_id, payment_id):
        self.cursor.execute("DELETE FROM payments WHERE chat_id = %s and payment_id = %s ", (chat_id, payment_id))
        self.connection.commit()

    def get_category_payments_current_month(self, chat_id, category_id):
        month_range = calendar.monthrange(datetime.date.year, datetime.date.month)
        first_day_of_month = month_range[0]
        last_day_of_month = month_range[1]
        self.cursor.execute("""SELECT c.*, sum(p.price) as amount
                            FROM categories as c
                            LEFT JOIN payments as p on p.category_id = c.category_id
                            WHERE c.chat_id = %s and date >= %s and c.date <= %s
                            group by c.category_id
                            ORDER BY c.position""",
                            (chat_id, first_day_of_month, last_day_of_month))
        self.connection.commit()
        return self.cursor.fetchall()

    def get_chat_payments_current_month(self, chat_id, first_day_of_month, last_day_of_month):
        self.cursor.execute("""SELECT c.*, COALESCE (SUM(p.price), 0) amount
                                FROM categories as c
                                LEFT JOIN payments as p on p.category_id = c.category_id 
                                    AND c.chat_id = %s and p.date >= %s and p.date <= %s
                                group by c.category_id
                                ORDER BY c.position""",
                            (chat_id, str(first_day_of_month), str(last_day_of_month)))
        return self.cursor.fetchall()
