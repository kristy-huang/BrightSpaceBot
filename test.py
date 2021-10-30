from bs_utilities import BSUtilities
from Authentication import get_brightspace_session_auto, setup_automation
from database.db_utilities import DBUtilities

bsu = BSUtilities()

dbu = DBUtilities("./database/db_config.py")
#setup_automation("test1", dbu)

auto_session = get_brightspace_session_auto("test1")
bsu.set_session_by_session(auto_session)
classes = bsu.get_classes_enrolled()
print(classes)