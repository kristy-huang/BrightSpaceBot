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
            "DESCRIPTION": str(description)
        }

        self._mysql.insert_into("NOTIFICATION_SCHEDULE", cols)


    def get_notifictaion_schedule(self, user_name):
        return self._mysql.general_command(f"SELECT DISTINCT TIME FROM NOTIFICATION_SCHEDULE WHERE USERNAME = \"{user_name}\"")


    def get_notifictaion_schedule_with_description(self, user_name):
        return self._mysql.general_command(f"SELECT DISTINCT TIME,DESCRIPTION FROM NOTIFICATION_SCHEDULE WHERE USERNAME = \"{user_name}\"")


    def clear_notification_schedule(self, user_name):
        self._mysql.delete("NOTIFICATION_SCHEDULE", f"USERNAME = \"{user_name}\"")


    def delete_notification_schedule(self, user_name, scheduled_time, decription):
        self._mysql.delete("NOTIFICATION_SCHEDULE", f"USERNAME = \"{user_name}\" AND TIME = \"{scheduled_time}\" AND DESCRIPTION = \"{decription}\"")


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

