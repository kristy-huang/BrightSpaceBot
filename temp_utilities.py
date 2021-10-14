from bs_utilities import BSUtilities
from database.db_utilities import DBUtilities
import datetime

#bsu = BSUtilities()
#bsu.set_session("xiong109", "1486,push")

user_col = {"USER_ID": None, 
            "FIRST_NAME": "katherine",
            "LAST_NAME": "xiong",
            "MAJOR": "cs",
            "CLASSES": "",
            "PIN": "123456",
            "STORAGE_METHOD": "",
            "STORAGE_PATH": ""}
cre_col = {
            "USER_ID": None,
            "USERNAME": "kxiondg",
            "PASSWORD": "1234",
            "BS_USERNAME": "xiong109",
            "BS_PASSWORD": "1486,push"
        }


bsu = BSUtilities()
bsu.set_session("xiong109", "1486,push")
dsu = DBUtilities()
dsu.connect_by_config("database/db_config.py")

utc_one_day_before = datetime.datetime.utcnow() - datetime.timedelta(days = 1)
utc_one_day_before = utc_one_day_before.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
announcements = bsu.get_announcements(since=utc_one_day_before)

notification = "Announcements from the past 24 hours: \n"
for announcement in announcements:
    # TODO: get a mapping from course id to course names from the database
    notification += "Class: {}\n".format(announcement['course_id'])
    notification += "{}\n\n".format(announcement['Title'])
    notification += "{}\n".format(announcement['Text'])
    pass
    
print(notification)
