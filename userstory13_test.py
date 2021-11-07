import unittest
from discord_config import config, USERNAME, PIN
from bs_api import BSAPI
from bs_utilities import BSUtilities

class Test_userstory13(unittest.TestCase):
    
    
    def test_validCase(self):
        #this is a completely valid case. Class exists, assignment exists, and there is feedback to be pulled.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        feedback = bs_utils.get_assignment_feedback("NUTR 303", "Recitation Assignment 1")
        self.assertNotIn("ERROR", feedback)
        self.assertNotIn("BOT REPORT", feedback)

    def test_NoFeedback(self):
        #when the class and assignment exist but there is no feedback provided.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        feedback = bs_utils.get_assignment_feedback("NUTR 303", "Recitation Assignment 2")
        self.assertNotIn("ERROR", feedback)
        self.assertIn("BOT REPORT: No feedback has been provided for this assignment.", feedback)
            
    def test_assignmentDNE(self):
        #when the class exists, but the assignment does not exist. Should return error message.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        feedback = bs_utils.get_assignment_feedback("CS 307", "Sprint 4 Retrospective Document")
        self.assertNotIn("BOT REPORT", feedback)
        self.assertIn("ERROR: Please make sure the assignment you have specified is spelled correctly and exists.", feedback)

    def test_classDNE(self):
        #when the provided class DNE.
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        feedback = bs_utils.get_assignment_feedback("CS 345", "Sprint 1 Retrospective Document")
        self.assertNotIn("BOT REPORT", feedback)
        self.assertIn("ERROR: Please make sure the course you have specified is spelled correctly and is a course that you are currently enrolled in.", feedback)

    def test_SubmissionsAccessDenied(self):
        #when the submissions for an assignment in a particular course cannot be accessed by the bot.
        #Permissions for coursepage is set by the owner (professor/instructor)
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        feedback = bs_utils.get_assignment_feedback("CS 307", "Sprint 1 Review")
        self.assertNotIn("ERROR", feedback)
        self.assertIn("BOT REPORT: I do not have permission to access these submissions.", feedback)

if __name__ == '__main__':
    unittest.main()
    #bs_utils = BSUtilities()
        #on_ready
        #bs_utils.set_session(USERNAME, PIN)
    #assert test_allTrue(bs_utils, "NUTR 303", "Recitation Assignment 1") == True

    #print("Everything passed")

    #   on_ready

