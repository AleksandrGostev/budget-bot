import sqlite3

conn = sqlite3.connect('db_budget.db')

cursor = conn.cursor()


cursor.execute("""CREATE TABLE payments (
                        payment_id integer primary key,
                        chat_id integer,
                        username text,
                        title text,
                        price real,
                        date text,
                        category_id integer
                )""")

cursor.execute("""CREATE TABLE categories (
                        category_id integer primary key,
                        chat_id integer,
                        payment_type text,
                        title text,
                        date text,
                        position integer
                )""")