from mysql_database import MySQLDatabase


class DBUtilities():
    def __init__(self):
        self._mysql = MySQLDatabase()

    def connect(self, host, username, password):
        self._mysql.connect(host, username, password)

    def connect_from_config(self, config_filename):
        self._mysql.connect_by_config(config_filename)


    # 
    def insert_user(self):
        pass

    