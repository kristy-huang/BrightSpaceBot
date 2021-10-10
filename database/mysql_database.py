import pymysql


class MySQLDatabase:
    def __init__(self):
        self._cursor = None

    # Connects to a mySQL cloud database instance with a given hostname, 
    # username & password. 
    #
    # return: a cursor pointing to a instance.

    def connect(self, host, username, password):
        db = pymysql.connect(host=host, user=username, passwd=password)
        cursor = db.cursor()
        self._cursor = cursor

    # Shows existing databases in the current instance
    #
    # cursor (pymysql.cursor): an cursor object pointing to a instance
    #
    # return: None

    def show_databases(self):
        sql = "SHOW DATABASES"
        state = self._cursor.execute(sql)
        if state:
            rows = self._cursor.fetchall()
            return rows
        return "No databases found in instance."

    # Creates a database with a given cursor and database name if no database
    # with a same name exists.
    # The change is commited automatically if there are no errors returned
    # by the instance.
    #
    # cursor (pymysql.cursor): an cursor object pointing to a instance
    # database_name (str): new database name
    #
    # return: None
    
    def create_database(self, database_name):
        sql = "CREATE DATABASE IF NOT EXISTS {database_name}".format(database_name=database_name)
        # Returns 1 for success
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()


    def drop_database(self, database_name):
        sql = "DROP DATABASE IF EXISTS {database_name}".format(database_name=database_name)
        # Returns 1 for success
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()

    # Makes the request to use a database
    #
    # cursor (pymysql.cursor): an cursor object pointing to a instance
    # database_name (str): database name
    #
    # return: None

    def use_database(self, database_name):
        sql = "USE {database_name}".format(database_name=database_name)
        self._cursor.execute(sql)


    # Creates a table within a database with a given table name, if no table
    # with a same name exists in the database.
    # The cursor passed in must be using a database before calling this function.
    # The columns variable is the list of variables used to create the table.
    # e.g. 
    # id int not null auto_increment,\n
    # fname text,\n
    # lname text
    #
    # The change is commited automatically if there are no errors returned
    # by the instance.
    #
    # cursor (pymysql.cursor): an cursor object pointing to a instance
    # table_name (str): new table name
    # columns (str): variables for creating the table
    #
    # return: None

    def create_table(self, table_name, columns):
        sql = "CREATE TABLE IF NOT EXISTS {table_name}\n({columns})".format(table_name=table_name, columns=columns)
        # Returns 1 for success
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()


    # Drops a table with a given cursor and table name if the table exists.
    # The change is commited automatically if there are no errors returned
    # by the instance.
    #
    # cursor (pymysql.cursor): an cursor object pointing to a instance
    # table_name (str): table name
    #
    # return: None

    def drop_table(self, table_name):
        sql = "DROP TABLE IF EXISTS {table_name}".format(table_name=table_name)
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()


    # Shows the existing tables in the current database
    #
    # cursor (pymysql.cursor): an cursor object pointing to a instance
    #
    # return: None

    def show_tables(self):
        sql = "SHOW TABLES"
        state = self._cursor.execute(sql)
        if state:
            rows = self._cursor.fetchall()
            return rows
        return "No databases found in instance."
