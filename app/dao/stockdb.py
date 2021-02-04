import sqlite3

from app.common.config import getDBFileURI


class DatabaseManager:
    #''' Database Manager '''

    def __init__(self):
        db_uri = getDBFileURI()
        self.db_name = db_uri  # database name
        self.conn = None       # connection

    def getConnection(self):
        return self.conn

    def check_database(self):
        #''' Check if the database exists or not '''

        try:
            print(f'Checking if {self.db_name} exists or not...')
            self.conn = sqlite3.connect(self.db_name, uri=True)
            print(f'Database exists. Succesfully connected to {self.db_name}')

        except sqlite3.OperationalError as err:
            print('Database does not exist')
            print(err)

    def close_connection(self):
        #''' Close connection to database '''

        if self.conn is not None:
            print('Database connection closed.')
            self.conn.close()

    def executeSQL(self, p_sql):

        if self.conn is not None:
            cur = self.conn.cursor()
            cur.execute(p_sql)
            self.conn.commit()
            print('SQL ' + p_sql + ' executed sucssfully')

    def querySQL(self, p_sql):

        if self.conn is not None:
            cur = self.conn.cursor()
            return cur.execute(p_sql)


