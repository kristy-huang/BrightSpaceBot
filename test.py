from database.db_utilities import DBUtilities

d = DBUtilities("./database/db_config.py")

print(d.show_table_content("USERS"))