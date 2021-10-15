"""from database.mysql_database import MySQLDatabase

sql = MySQLDatabase()
sql.connect("bsbot.cgiajlg2cozl.us-east-2.rds.amazonaws.com", "admin", "b&IWmx.12f0sm")"""
"""sql.create_database("BSBOT")
sql.use_database("BSBOT")
sql.create_table("USER_LIST", "user_id INT NOT NULL auto_increment PRIMARY KEY,\n username text,\nname text")
cmd = "id int not null auto_increment PRIMARY KEY,\n user_id int,\ncourse_id text,\ntitle text,\nevent_type text,\n"
cmd += "description text,\n start_date text"
sql.create_table("NOTIFICATIONS", cmd)
"""

"""sql.use_database("BSBOT")
cmd = "id int not null auto_increment PRIMARY KEY,\nuser_id int,\ncourse_id text,\ntitle text,\n"
cmd += "text text,\n start_date text"
sql.create_table("ANNOUNCEMENTS", cmd)
print(sql.show_tables())"""

