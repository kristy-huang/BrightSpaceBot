import unittest
from bs_api import BSAPI
from .test_config import username, password


class TestGetGrades(unittest.TestCase):

    def test_get_all_assignments_in_gradebook(self):
        _bs_api = BSAPI()
        _bs_api.set_session(username, password)
        course_id = 335757  # cs307
        result = _bs_api.get_all_assignments_in_gradebook(course_id)
        proj_charter_assignment_id = 1537997
        self.assertIsNotNone(result, "Graded assignments found")
        self.assertEqual(proj_charter_assignment_id, result[0])

    def test_get_all_assignments_in_gradebook_no_grades(self):
        _bs_api = BSAPI()
        _bs_api.set_session(username, password)
        course_id = 255533  # Spring 2021 SI
        result = _bs_api.get_all_assignments_in_gradebook(course_id)
        self.assertEqual(result, [], "No graded assignments found")

    def test_get_grade_of_assignment_found(self):
        _bs_api = BSAPI()
        _bs_api.set_session(username, password)
        course_id = 335757  # cs307
        proj_charter_assignment_id = 1537997
        assignment_name = 'Project Charter Document'
        grade = '100 %'
        result = _bs_api.get_grade_of_assignment(course_id, proj_charter_assignment_id)
        self.assertIsNotNone(result, "Grade found")
        self.assertEqual(proj_charter_assignment_id, result[0])
        self.assertEqual(course_id, result[1])
        self.assertEqual(assignment_name, result[2])
        self.assertEqual(grade, result[3])


if __name__ == '__main__':
    unittest.main()
