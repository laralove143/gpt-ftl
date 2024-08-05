import sqlite3
from fluent.syntax.ast import Message


class Db:
    def __init__(self):
        self.conn = sqlite3.connect("./cache.sqlite")
        self.c = self.conn.cursor()
        self.c.execute("CREATE TABLE IF NOT EXISTS translated_messages (message TEXT)")
        self.conn.commit()

    def insert_ftl_file(self, file):
        messages = [
            (file.content[message.span.start : message.span.end],)
            for message in file.body
            if isinstance(message, Message)
        ]

        self.c.executemany("INSERT INTO translated_messages VALUES (?)", messages)
        self.conn.commit()

    def get_messages(self):
        return self.c.execute("SELECT message FROM translated_messages").fetchall()
