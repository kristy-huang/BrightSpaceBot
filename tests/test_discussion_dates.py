from bs_utilities import BSUtilities
from discord_config import USERNAME, PIN
from bs_calendar import Calendar


def check_due_dates_EAPS(bs):
    upcoming = bs.get_discussion_due_dates_TEST()
    due = bs.process_upcoming_dates(upcoming)
    print(due)

    array = [['Casual Conversation', '2021-12-05T04:59:59.000Z']]
    counter = 0
    for d in due:
        assert array[counter][0] == d[0]
        assert array[counter][1] == d[1]
        counter = counter + 1


def check_event_details(event_name, end_date):
    calendar = Calendar()
    vals = calendar.get_event_from_name(event_name)

    assert vals[1] == end_date


if __name__ == '__main__':
    bs = BSUtilities()
    bs.set_session(USERNAME, PIN)

    check_due_dates_EAPS(bs)

    event_name = "DISCUSSION POST DUE: Casual Conversation (336112)"
    date = "2021-12-05T23:59:59-05:00"

    check_event_details(event_name, date)

    print("Everything passed")
