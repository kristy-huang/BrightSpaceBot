import unittest
from bs_utilities import BSUtilities
from .test_config import username, password
from bs_calendar import Calendar
import json
import datetime


class TestGetQuizzesCalendar(unittest.TestCase):
    def test_get_upcoming_quizzes(self):
        _bs_utils = BSUtilities()
        _bs_utils.set_session(username, password)
        course_id = 335796  # cs381
        result = _bs_utils.get_all_upcoming_quizzes()
        print(result)
        self.assertEqual(result[0]['course_id'], course_id)
        self.assertEqual(result[0]['course_name'], 'Fall 2021 CS 38100-LE2 LEC')
        self.assertEqual(result[0]['quiz_name'], 'Fall 2021 Quiz 08')
        self.assertEqual(result[0]['due_date'], '2021-10-27T03:59:00.000Z')

    def test_calls_to_calendar(self):
        cal = Calendar()
        file = open("./tests/calendar_test_data.json")
        quiz = json.load(file)
        # print(quiz['Name'])
        date = datetime.datetime.fromisoformat(quiz['DueDate'][:-1])
        end = date.isoformat()
        start = (date - datetime.timedelta(hours=1)).isoformat()
        event_title = quiz['Name']
        event_id, end_time = cal.get_event_from_name(event_title)

        # event has already been created in google calendar
        if event_id == -1:
            # insert new event to calendar
            cal.insert_event(event_title, "Unit test for adding event", start, end)
        # event has not been created
        else:
            # if end time has changed, update the event
            if end_time != end:
                cal.delete_event(event_id)
                cal.insert_event(event_title, "Unit test for adding event", start, end)


if __name__ == '__main__':
    unittest.main()
