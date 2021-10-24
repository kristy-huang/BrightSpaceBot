from database.db_utilities import DBUtilities

d = DBUtilities("./database/db_config.py")

print(d.get_notifictaion_schedule("a"))