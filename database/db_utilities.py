from database.mysql_database import MySQLDatabase
import hashlib


class DBUtilities():
    def __init__(self):
        self._mysql = MySQLDatabase()

    def connect(self, host, username, password):
        self._mysql.connect(host, username, password)

    def connect_by_config(self, config_filename):
        self._mysql.connect_by_config(config_filename)

    def use_database(self, database):
        self._mysql.use_database(database)

    def update_md5(self, table, col_name, new_val):
        pass

    def show_table_content(self, table, condition=None):
        sql = "SELECT * FROM {t}".format(t=table)
        sql += "WHERE {c}".format(condition) if condition else ""
        res = self._mysql.general_command(sql)
        res = str(res)
        res = res.replace("), (", "),\n(")
        return res

      
    def get_bs_cridential(self, user_id):
        sql = "SELECT BS_USERNAME , BS_PASSWORD FROM CREDENTIALS WHERE USER_ID = {}".format(user_id)
        res = self._mysql.general_command(sql)
        return res[0] if res else None

    '''
        Inserts a row into the USER table & CREDENTIALS table.
        pin and password will be encypted using md5.
        bs password would not.
        Works with any number of columns provided - even with 2 empty dictionaries


        user_cols: 
        {"USER_ID": null, (Can left to be blank!)
        "FIRST_NAME": VARCHAR(50),
        "LAST_NAME": VARCHAR(50),
        "MAJOR": VARCHAR(50),
        "CLASSES": TEXT,
        "PIN": VARCHAR(128) (encrypted),
        "STORAGE_METHOD": VARCHAR(10),
        "STORAGE_PATH": TEXT
        }


        credential_cols:
        {
            "USER_ID": null,
            "USERNAME": VARCHAR(50),
            "PASSWORD": VARCHAR(255) (encrypted),
            "BS_USERNAME": VARCHAR(50),
            "BS_PASSWORD": VARCHAR(255)
        }


        returns: 
            Success: the user id of the new added user.
            Fail: -1
    '''

    
    def insert_user(self, user_cols, credential_cols):

        if not user_cols:
            user_cols = {}
        if not credential_cols:
            credential_cols = {}

        # check if the same username exists:
        if "USERNAME" in credential_cols.keys():
            username = credential_cols["USERNAME"]
            sql = "SELECT user_id FROM CREDENTIALS WHERE USERNAME = '{}'".format(username)
            res = self._mysql.general_command(sql)

            
            if res and res[0]:
                print("Username already exsists.")
                return -1

        user_cols["USER_ID"] = None

        if "PIN" in user_cols.keys():
            user_cols["PIN"] = self.get_encrypted(user_cols["PIN"])
        if "PASSWORD" in credential_cols.keys():
            credential_cols["PASSWORD"] = self.get_encrypted(credential_cols["PASSWORD"])


            
        self._mysql.insert_into("USERS", user_cols)
        user_id = self._mysql.get_last_inserted_id()

        credential_cols["USER_ID"] = user_id

        self._mysql.insert_into("CREDENTIALS", credential_cols)

        return user_id


      
    def get_encrypted(self, string):
        string = string.encode('utf-8')
        string = hashlib.md5(string).hexdigest()
        return string



    '''
        Resets an auto increment back to 1
    '''

    def reset_auto_increment(self, table_name, auto_id_name):
        sql = "ALTER TABLE {t} DROP COLUMN {id};".format(t=table_name, id=auto_id_name)
        self._mysql.general_command(sql)
        sql = "ALTER TABLE {t} ADD COLUMN {id} INT NOT NULL AUTO_INCREMENT PRIMARY KEY;".format(t=table_name,
                                                                                                id=auto_id_name)
        self._mysql.general_command(sql)


        
    def clear_table(self, table_name, auto_id_name=None):
        self._mysql.delete(table_name)
        if auto_id_name:
            self.reset_auto_increment(table_name, auto_id_name)

if __name__ == '__main__':
    s = DBUtilities()
    s.connect_by_config("db_config.py")
    s.use_database("BSBOT")
    print(s.show_table_content("PREFERENCES"))
    DB_USERNAME = "currymaster"
    sql_command = f"SELECT STORAGE_LOCATION FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
    sql_result = s._mysql.general_command(sql_command)[0][0]
    print(sql_result)
