from database.mysql_database import MySQLDatabase


class DBUtilities():
    def __init__(self, db_config):
        self._mysql = MySQLDatabase(db_config)


    def add_notifictaion_schedule(self, user_name, scheduled_time, interval_time, channel_id, description=""):
        cols = {
            "USERNAME": user_name,
            "TIME": scheduled_time,
            "TIME_INTERVAL": interval_time,
            "CHANNEL_ID": channel_id,
            "DESCRIPTION": str(description),
            "TYPES": "1111"
        }

        self._mysql.insert_into("NOTIFICATION_SCHEDULE", cols)


    def get_notifictaion_schedule(self, user_name):
        return self._mysql.general_command(f"SELECT DISTINCT TIME FROM NOTIFICATION_SCHEDULE WHERE USERNAME = \"{user_name}\"")


    def get_notifictaion_schedule_with_description(self, user_name):
        return self._mysql.general_command(f"SELECT DISTINCT TIME,DESCRIPTION,TYPES FROM NOTIFICATION_SCHEDULE WHERE USERNAME = \"{user_name}\" ORDER BY DESCRIPTION ASC")


    def clear_notification_schedule(self, user_name):
        self._mysql.delete("NOTIFICATION_SCHEDULE", f"USERNAME = \"{user_name}\"")


    def delete_notification_schedule(self, user_name, scheduled_time, decription):
        self._mysql.delete("NOTIFICATION_SCHEDULE", f"USERNAME = \"{user_name}\" AND TIME = \"{scheduled_time}\" AND DESCRIPTION = \"{decription}\"")


    def update_notification_schedule_types(self, user_name, scheduled_time, decription, new_types):
        cols = {"TYPES": new_types}
        self._mysql.update("NOTIFICATION_SCHEDULE", cols, f"USERNAME = \"{user_name}\" AND TIME = \"{scheduled_time}\" AND DESCRIPTION = \"{decription}\"")


    def add_class_schedule(self, user_name, course_name, scheduled_time, description=""):
        cols = {
            "USERNAME": user_name,
            "TIME": scheduled_time,
            "COURSE_NAME": course_name,
            "DESCRIPTION": str(description)
        }

        self._mysql.insert_into("CLASS_SCHEDULE", cols)


    def get_class_schedule_with_description(self, user_name):
        return self._mysql.general_command(f"SELECT DISTINCT COURSE_NAME,TIME,DESCRIPTION FROM CLASS_SCHEDULE WHERE USERNAME = \"{user_name}\" ORDER BY COURSE_NAME, DESCRIPTION ASC, TIME ASC")


    def get_classes_in_schedule(self, user_name):
        res = self._mysql.general_command(f"SELECT DISTINCT COURSE_NAME FROM CLASS_SCHEDULE WHERE USERNAME = \"{user_name}\"")
     
        res = list(res)
        if res:
            for i in range(len(res)):
                res[i] = res[i][0]

        return res       

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

    def add_hotp_secret_counter(self, user_name, hotp_secret, counter):
        if self._mysql.general_command(f"SELECT * FROM CREDENTIALS WHERE USERNAME = \"{user_name}\""):
            self.update_hotp_secret_counter(user_name, hotp_secret, counter)
        else:
            self.insert_hotp_secret_counter(user_name, hotp_secret, counter)


    def insert_hotp_secret_counter(self, user_name, hotp_secret, counter):
        cols = {
            "USERNAME": user_name,
            "hotp_secret": hotp_secret,
            "hotp_counter": counter
        }
        
        self._mysql.insert_into("CREDENTIALS", cols)


    def update_hotp_secret_counter(self, user_name, hotp_secret, counter):
        cols = {
            "hotp_secret": hotp_secret,
            "hotp_counter": counter
        }
        
        self._mysql.update("CREDENTIALS", cols, "username = \"{}\"".format(user_name))


    def get_hotp_secret_counter(self, user_name):
        return self._mysql.general_command(f"SELECT DISTINCT hotp_secret,hotp_counter FROM CREDENTIALS WHERE USERNAME = \"{user_name}\"")


    def increase_hotp_counter(self, user_name):
        return self._mysql.general_command(f"UPDATE CREDENTIALS SET hotp_counter = hotp_counter + 1 WHERE USERNAME = \"{user_name}\"")


    def update_bs_username_pin(self, user_name, bs_username, bs_pin):
        cols = {
            "BS_USERNAME": bs_username,
            "bs_pin": bs_pin
        }
        
        self._mysql.update("CREDENTIALS", cols, "username = \"{}\"".format(user_name))


    def add_bs_username_pin(self, user_name, bs_username, bs_pin):
        if self._mysql.general_command(f"SELECT * FROM CREDENTIALS WHERE USERNAME = \"{user_name}\""):
            self.update_bs_username_pin(user_name, bs_username, bs_pin)
        else:
            self.insert_bs_username_pin(user_name, bs_username, bs_pin)


    def insert_bs_username_pin(self, user_name, bs_username, bs_pin):
        cols = {
            "USERNAME": user_name,
            "BS_USERNAME": bs_username,
            "bs_pin": bs_pin
        }
        
        self._mysql.insert_into("CREDENTIALS", cols)


    def get_bs_username_pin(self, user_name):
        return self._mysql.general_command(f"SELECT DISTINCT BS_USERNAME,bs_pin FROM CREDENTIALS WHERE USERNAME = \"{user_name}\"")


    # Gets all scheduled notification time for all users by a given time. 
    #
    # time_string (str): represents the requested time, in the formatof HH:MM (e.g. 09:04)
    # weekday (int): represents 
    def get_notifictaion_schedule_by_time(self, time_string, weekday):
        schedules = self._mysql.general_command("SELECT DISTINCT USERNAME,CHANNEL_ID,TYPES FROM NOTIFICATION_SCHEDULE WHERE TIME = \"{}\" AND (DESCRIPTION = {} OR DESCRIPTION = 7)".format(time_string, weekday))
        #print(schedules)
        if schedules:
            return schedules
        else:
            return []


    def get_discord_user_password(self, username):
        res = self._mysql.general_command(f"SELECT USERNAME, PASSWORD FROM USERS WHERE USERNAME = \"{username}\"")
        return res


    def change_username(self, table_name, old_username, new_username):
        res = self._mysql.general_command(f"UPDATE {table_name} SET USERNAME = \"{new_username}\" WHERE USERNAME = \"{old_username}\"")


    # If a user exists in the USER table, return the username & encoded password 
    # Returns None if it does not.
    # username: str

    def get_username_password(self, username):
        res = self._mysql.general_command(f"SELECT username, password FROM USERS WHERE username = \"{username}\"")
        return res




    # description: weekday!
    def add_download_shcedule(self, username, scheduled_time, type, description, user_id):
        cols = {
            "USERNAME": username,
            "TIME": scheduled_time,
            "TYPE": type,
            "DESCRIPTION": str(description),
            "user_id": user_id
        }

        self._mysql.insert_into("DOWNLOAD_SCHEDULE", cols)


    def get_download_schedule(self, username):
        return self._mysql.general_command(f"SELECT DISTINCT TIME,DESCRIPTION,TYPE FROM DOWNLOAD_SCHEDULE WHERE USERNAME = \"{username}\" ORDER BY TIME ASC")


    def get_download_schedule_by_time(self, time_string):
        return self._mysql.general_command(f"SELECT DISTINCT user_id,TYPE FROM DOWNLOAD_SCHEDULE WHERE TIME = \"{time_string}\"")

    def clear_download_schedule(self, user_name):
        self._mysql.delete("DOWNLOAD_SCHEDULE", f"USERNAME = \"{user_name}\"")


