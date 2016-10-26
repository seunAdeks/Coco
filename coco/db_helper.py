import sqlite3
from config import *
from flask import g

class DBAssistant:

    # def __init__(self):
    #     with app.app_context():
    #         self.__init_db()

    def __connect_db(self):
        """

        Connects to the database
        :param null
        :var rv - the database instance
        :return rv

        """
        rv = sqlite3.connect(app.config['DATABASE'])
        rv.row_factory = sqlite3.Row
        return rv


    def __get_db(self):
        """
        Gets the database instance and returns it.
        :var g.sqlite_db the database instance gotten from connect_db
        :return: g.sqlite_db

        """
        if not hasattr(g, 'sqlite_db'):
            g.sqlite_db = self.__connect_db()
        return g.sqlite_db


    def __init_db(self):
        """
        Initializes the database.
        :var db - the instances from get_db
        :return: null

        """

        db = self.__get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        self.db = db


    def close_db(Self):
        """
        :param error:
        :return:
        """
        with app.app_context():
            if hasattr(g, 'sqlite_db'):
                g.sqlite_db.close()


    def insert_single(self, table, column, value):
        db = self.__get_db()
        sql = "insert into " + table + " ("+ column +") values (\""+value+"\")"
        db.execute(sql)
        db.commit()


    def get_single(self, sql, param=None):
        """
        Fetches one row from database with given sql query
        """
        db = self.__get_db()
        if param is None:
            cur = db.execute(sql)
            m = cur.fetchone()
        else:
            cur = db.execute(sql, param)
            m = cur.fetchone()
        return m


    def get_all(self, sql, param = None):
        """
        Fetches all matching rows from database with given sql query
        """
        db = self.__get_db()
        if param is None:
            cur = db.execute(sql)
        else:
            cur = db.execute(sql, param)
        m = cur.fetchall()
        return m


    def change_data(self, sql, param=None):
        """
        Updates, inserts, deletes data in the DB with given sql query
        :param sql:
        :param param:
        :return:
        """
        db = self.__get_db()
        if param is None:
            db.executemany(sql)
        else:
            db.executemany(sql, param)
        db.commit()


    def update(self, sql, param):
        db = self.__get_db()
        db.execute(sql, param)
        db.commit()
