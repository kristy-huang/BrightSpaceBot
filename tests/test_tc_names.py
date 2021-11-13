from bot_responses import BotResponses
from database.db_utilities import DBUtilities


def test_if_tc_exists(request_tc, br, username):
    return br.check_if_tc_exists(request_tc, username)


if __name__ == '__main__':
    bot_response = BotResponses()
    database = DBUtilities()
    username = "currymaster"
    config_file = "/Users/raveena/Desktop/BrightSpaceBot/database/db_config.py"
    database.connect_by_config(config_file)
    database.use_database("BSBOT")
    bot_response.set_DB_param(database)

    # Channels that do not exist
    requested_tc = "Some random channel name"
    assert test_if_tc_exists(requested_tc, bot_response, username) == False
    requested_tc = "CS 307"
    assert test_if_tc_exists(requested_tc, bot_response, username) == False
    requested_tc = "CS 320"
    assert test_if_tc_exists(requested_tc, bot_response, username) == False
    requested_tc = "Too much homework in school"
    assert test_if_tc_exists(requested_tc, bot_response, username) == False
    requested_tc = "deadlines"
    assert test_if_tc_exists(requested_tc, bot_response, username) == False
    requested_tc = "worklife"
    assert test_if_tc_exists(requested_tc, bot_response, username) == False

    requested_tc = "dead"
    assert test_if_tc_exists(requested_tc, bot_response, username) == True
    requested_tc = "grades"
    assert test_if_tc_exists(requested_tc, bot_response, username) == True
    requested_tc = "general"
    assert test_if_tc_exists(requested_tc, bot_response, username) == True
    requested_tc = "storage"
    assert test_if_tc_exists(requested_tc, bot_response, username) == True

    print("Everything passed")
