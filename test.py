'''from bs_utilities import BSUtilities
from Authentication import get_brightspace_session_auto
from database.db_utilities import DBUtilities

bsu = BSUtilities()

dbu = DBUtilities("./database/db_config.py")
#setup_automation("test1", dbu)

#auto_session = get_brightspace_session_auto("test1")
bsu.set_session_auto(dbu, "test1")
classes = bsu.get_classes_enrolled()
print(classes)'''

import datetime

now = datetime.datetime.now()
hour = now.hour
minute = now.minute
weekday = now.weekday()
t = now.strftime("%H:%M")
from database.db_utilities import DBUtilities
t = "12:22"
print(weekday)
dbu = DBUtilities("./database/db_config.py")
print(dbu.get_notifictaion_schedule_by_time(t, weekday))