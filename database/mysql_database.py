import pymysql


class MySQLDatabase:
    def __init__(self):
        self._cursor = None



    '''
        Connects to a mySQL cloud database instance with a given hostname, 
        username & password. 

        return: None
    '''
    def connect(self, host, username, password):
        db = pymysql.connect(host=host, user=username, passwd=password)
        cursor = db.cursor()
        self._cursor = cursor
        

    '''
        Connects to a mySQL cloud database instance using a config file. 
        see the example for the format.
        
        return: None
    '''
    def connect_by_config(self, config_filename):
        conf_dict = eval(open(config_filename).read())
        self.connect(host=conf_dict['host'], 
                     username=conf_dict['username'],
                     password=conf_dict['passwd'])


    '''
        Shows existing databases in the current instance

        return: String, showing the databases.
    '''
    def show_databases(self):
        sql = "SHOW DATABASES"
        state = self._cursor.execute(sql)
        if state:
            rows = self._cursor.fetchall()
            return rows
        return "No databases found in instance."


      
    '''
        Creates a database with a given cursor and database name if no database
        with a same name exists.
        The change is commited automatically if there are no errors returned
        by the instance.

        database_name (str): new database name

        return: None
    '''

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


    '''
        Makes the request to use a database
        
        database_name (str): database name
        
        return: None
    '''
    def use_database(self, database_name):
        sql = "USE {database_name}".format(database_name=database_name)
        self._cursor.execute(sql)

    '''
        Creates a table within a database with a given table name, if no table
        with a same name exists in the database.
        The cursor passed in must be using a database before calling this function.
        The columns variable is the list of variables used to create the table.
        e.g. 
        id int not null auto_increment,\n
        fname text,\n
        lname text

        The change is commited automatically if there are no errors returned
        by the instance.

        table_name (str): new table name
        columns (str): variables for creating the table

        return: None
    '''

    def create_table(self, table_name, columns):
        sql = "CREATE TABLE IF NOT EXISTS {table_name}\n({columns})".format(table_name=table_name, columns=columns)
        # Returns 1 for success
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()

    '''
        Drops a table with a given cursor and table name if the table exists.
        The change is commited automatically if there are no errors returned
        by the instance.

        table_name (str): table name

        return: None
    '''

    def drop_table(self, table_name):
        sql = "DROP TABLE IF EXISTS {table_name}".format(table_name=table_name)
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()

    '''
        Shows the existing tables in the current database

        return: String, showing the tables.
    '''

    
    def show_tables(self):
        sql = "SHOW TABLES"
        state = self._cursor.execute(sql)
        if state:
            rows = self._cursor.fetchall()
            return rows
        return "No tables found in database."


    '''
        Inserts a column into a specific table. Very basic functionality. Does no gate
        keeping.
        
        table_name(str): table to insert into
        cols(dict): in the format of:
        {auto_increment column: None, 
        column name 1: value 1,
        column name 2: value 2}

        returns: None
    '''

    def insert_into(self, table_name, cols):

        # print(cols)
        if not table_name:
            return

        columns = ""
        values = ""
        for col in cols.keys():
            columns += str(col) + ","
            val = cols[col]
            if not val:
                values += "null,"
            elif isinstance(val, str):
                values += "\'" + str(cols[col]) + "\',"
            else:
                values += str(cols[col]) + ","
        columns = columns[:-1]
        values = values[:-1]

        # print(columns)
        # print(values)
        sql = "INSERT INTO {tb_n} ({cols})\nVALUES ({vals})".format(tb_n=table_name,
                                                                    cols=columns,
                                                                    vals=values)

        # Returns 1 for success
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()


            
    def delete(self, table_name, condition=None):
        if not table_name:
            return
        sql = "DELETE FROM {tb_n}".format(tb_n=table_name)

        
        if condition:
            sql += " WHERE {cond}".format(cond=condition)

        state = self._cursor.execute(sql)
        self._cursor.connection.commit()


    '''
        Inserts a column into a specific table. Very basic functionality. Does no gate
        keeping.
        table_name(str): table to insert into
        cols(dict): in the format of:
        {auto_increment column: None, 
        column name 1: value 1,
        column name 2: value 2}

        returns: None
    '''

    def update(self, table_name, cols, condition):
        if not cols:
            return

        set_cols = ""
        for col in cols.keys():
            print(col, str(cols[col]) )

            set_cols += col + "="
            if isinstance(cols[col], str):
                set_cols += "\"" + str(cols[col]) + "\","
            else:
                set_cols += str(cols[col]) + ","

            print(set_cols)
        set_cols = set_cols[:-1]

        sql = "UPDATE {tb_n}\nSET {set_cols}".format(tb_n=table_name,
                                                     set_cols=set_cols)
        sql += "\nWHERE {cond};".format(cond=condition) if condition else ""

        print(sql)
        state = self._cursor.execute(sql)
        if state:
            self._cursor.connection.commit()

    # returns the last auto incremented id
    def get_last_inserted_id(self):
        sql = "SELECT LAST_INSERT_ID()"

        
        state = self._cursor.execute(sql)
        if state:
            rows = self._cursor.fetchall()
            return rows[0][0]
        return -1


      
    def general_command(self, command):
        state = self._cursor.execute(command)
        self._cursor.connection.commit()
        rows = self._cursor.fetchall()
        return rows


    '''
        find rows with one attribute
        
        return the rows if found, else return -1 if query returns empty
    '''
    def find_rows_one_attr(self, table_name, col, condition):
        sql = 'SELECT * FROM {table_name} WHERE {col} = {condition}'.format(table_name=table_name,
                                                                            col=col,
                                                                            condition=condition)
        state = self._cursor.execute(sql)
        if state == 1:
            rows = self._cursor.fetchall()
            # print(rows)
            return rows
        elif state == 0:
            return -1
