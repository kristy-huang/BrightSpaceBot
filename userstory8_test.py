import unittest
from discord_config import config, USERNAME, PIN
from bs_api import BSAPI
from bs_utilities import BSUtilities

class Test_userstory8(unittest.TestCase):
    def test_validCase(self):
        #when the student being searched for exists in a given class.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        output = bs_utils.search_for_student_in_class("NUTR 303", "Brittany Butler")
        self.assertTrue(output)
    
    def test_studentDNE(self):
        #when the student being searched for does not exist in a given class.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        output = bs_utils.search_for_student_in_class("CS 307", "Mitch Daniels")
        self.assertFalse(output)

    def test_classDNE(self):
        #when the class being provided for search is incorrectly spelled/does not exist as one of the user’s enrolled courses.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        output = bs_utils.search_for_student_in_class("EAPS 113", "Shaun Thomas")
        self.assertFalse(output)
    
    def test_inputsAreCaps(self):
        #when the inputs  - class and student name are typed in all caps.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        output = bs_utils.search_for_student_in_class("MA 265", "JOHNNY SHEN")
        self.assertTrue(output)

    def test_inputsAreLowercase(self):
        #when the inputs - class and student name are typed in lowercase.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        output = bs_utils.search_for_student_in_class("entr 310", "sarah whisman")
        self.assertTrue(output)
    
    def test_inputsAreDifferentCases(self):
        #when the inputs - class and student name are in different cases.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        output = bs_utils.search_for_student_in_class("MA 265", "joHnNy SHeN")
        self.assertTrue(output)

    

if __name__ == '__main__':
    unittest.main()
    #bs_utils = BSUtilities()
        #on_ready
        #bs_utils.set_session(USERNAME, PIN)
    #assert test_allTrue(bs_utils, "NUTR 303", "Recitation Assignment 1") == True

    #print("Everything passed")

    #   on_ready