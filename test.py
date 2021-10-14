from database.mysql_database import MySQLDatabase

sql = MySQLDatabase()
sql.connect_by_config("database/db_config.py")

sql.use_database("BSBOT")
#sql.update("CLASSES", {"COURSE_NAME":"asd"}, "COURSE_ID = '12345'")
sql.insert_into("USERS", {'FIRST_NAME': 'k', 'LAST_NAME': 'x'})
#sql.delete("CLASSES", "COURSE_ID = '12345'")
print(sql.show_tables())
print(sql.general_command("SELECT * FROM USERS"))
