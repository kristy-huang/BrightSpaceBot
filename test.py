


def db_showcase():
    from database.mysql_database import MySQLDatabase

    sql = MySQLDatabase()
    sql.connect_by_config("database/db_config.py")

    sql.use_database("BSBOT")
    print(sql.show_tables())
    print(sql.general_command("SELECT * FROM USERS"))


def auth_showcase():
    from authentication import get_brightspace_session
    from bs_api import BSAPI
    from discord_config import USERNAME, PIN, PIN_WRONG


    session = get_brightspace_session(USERNAME, PIN)
    print(session)
    bs_api = BSAPI()
    bs_api.set_session_by_object(session)
    print(bs_api.get_enrollments())


auth_showcase()