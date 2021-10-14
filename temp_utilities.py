from bs_utilities import BSUtilities
from database.db_utilities import DBUtilities

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

dbu = DBUtilities()
dbu.connect_by_config("database/db_config.py")
dbu.use_database("BSBOT")
#print(dbu.get_bs_cridential("8"))
#user_id = dbu.insert_user(user_col, cre_col)
#dbu.clear_table("USERS")
#dbu.clear_table("CREDENTIALS")
#print(dbu.show_table_content("USERS"))

def store_all_past_notifications(user_id):
    pass
    
    # TODO: login the user

    cridentials = dbu.get_bs_cridential(user_id)
    bsu = BSUtilities()
    bsu.set_session(cridentials[0], cridentials[1])
    announcements = bsu.get_announcements()
    print(announcements)

store_all_past_notifications("8")