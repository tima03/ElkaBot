import re
import psycopg2
from decouple import config
from psycopg2.extras import Json
import json
import logging


class PostgresHandler:
    def __init__(self, db_url=None):
        self.db_url = db_url or config('PG_LINK')
        self.conn = None
        self._parse_database_url()

    def _parse_database_url(self):
        # Регулярное выражение для парсинга строки подключения
        pattern = re.compile(
            r'postgresql://(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>[^/]+)/(?P<dbname>.+)'
        )
        match = pattern.match(self.db_url)
        if match:
            self.username = match.group('username')
            self.password = match.group('password')
            self.host = match.group('host')
            self.port = match.group('port')
            self.dbname = match.group('dbname')

    async def connect_by_link(self):
        # Подключение к базе данных
        try:
            self.conn = psycopg2.connect(self.db_url)
        except psycopg2.DatabaseError as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return False
        return True

    async def connect_by_UPHD(self):
        try:
            self.conn = psycopg2.connect(dbname=self.dbname, user=self.username, password=self.password, host=self.host,
                                         port=self.port)
        except psycopg2.DatabaseError as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return False
        return True

    async def disconnect(self):
        # Отключение от базы данных
        if self.conn:
            self.conn.close()
            return True
        else:
            return False

    def insert_into_table(self, table, data):
        # Вставка данных в таблицу
        with self.conn.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(data))
            columns = ', '.join(data.keys())
            values = tuple(data.values())
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, values)
            self.conn.commit()

    def update_table(self, table, data, condition):
        # Обновление данных в таблице
        with self.conn.cursor() as cursor:
            set_clause = ', '.join([f"{k} = %s" for k in data])
            values = tuple(data.values())
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            cursor.execute(query, values)
            self.conn.commit()
