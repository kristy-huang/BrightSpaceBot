from bs_utilities import BSUtilities
from discord_config import USERNAME, PIN


def check_eaps_assignments(courseID, bs):
    upcoming = bs._bsapi.get_upcoming_assignments(courseID)
    due = bs.process_upcoming_dates(upcoming)
    for d in due:
        assert d[0] == "Project topic proposal"
        assert d[1] == "2021-11-06T03:59:00.000Z"


def check_cs307_assignments(courseID, bs):
    array = [['Sprint 2 Review', '2021-11-06T03:58:00.000Z'], ['Sprint 2 Retrospective Document', '2021-11-09T04:58:00.000Z'],['Sprint 3 Planning Document', '2021-11-10T04:58:00.000Z'], ['Sprint 3 Review', '2021-12-04T04:58:00.000Z'], ['Sprint 3 Retrospective Document', '2021-12-07T04:58:00.000Z']]

    upcoming = bs._bsapi.get_upcoming_assignments(courseID)
    due = bs.process_upcoming_dates(upcoming)
    counter = 0
    for d in due:
        assert array[counter][0] == d[0]
        assert array[counter][1] == d[1]
        counter = counter + 1


if __name__ == '__main__':
    bs = BSUtilities()
    bs.set_session(USERNAME, PIN)

    check_eaps_assignments("336112", bs)
    check_cs307_assignments("335757", bs)

    print("Everything passed")

