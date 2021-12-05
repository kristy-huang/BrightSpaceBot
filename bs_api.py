from Authentication import get_brightspace_session, get_brightspace_session_auto

import requests
import os
import json
import datetime

class BSAPI():
    # ---------- Some initialization functions -----------

    # debug (bool): if set to True, debug messages for API calls will be enabled.
    def __init__(self, debug=False):
        self._session = None
        self._debug = debug
        self._API_URL_PREFIX = "https://purdue.brightspace.com/d2l/api/"
        self._HEADER = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }


    # Logs in to BS automatically
    #
    # dbu (DBUtilities object): a DBUtilities object connected to a database
    # discord_username (str): discord username

    def set_session_auto(self, dbu, discord_username):
        self._session = get_brightspace_session_auto(dbu, discord_username)

    def set_session_by_session(self, session):
        if not session:
            raise ValueError("Session provided is Null.")

        if type(session) != type(requests.session()):
            raise ValueError("Session provided is not a request.session instance.")
        self._session = session

    def set_session(self, username, password):
        self._session = get_brightspace_session(username=username, password=password)

    '''
        ---------- Actual API call functions! -----------

        All functions in the section returns None if the current session is None, or 
        there is an error (e.g. 404 not found) when trying to retrieve the data.
        All functions returns a dictionary. Please see the reference pages for more
        information.
    '''

    '''
        Pulls user "who am i" information.
        
        returns: WhoAmIUser JSON
    '''

    def get_user_info(self):
        url = self._API_URL_PREFIX + "lp/1.21/users/whoami"
        return self.__process_api_json("get_user_info", url)

    '''
        Pulls all organizations (classes, groups, etc.) the user is enrolled in
        return: an array of JSON blocks
    '''

    def get_enrollments(self):
        url = self._API_URL_PREFIX + "lp/1.26/enrollments/myenrollments/"
        return self.__process_api_json("get_enrollments", url)

    '''
        Pulls all quiz information from BrightSpace with a given course id.

        course_id (str / int): the id of the course

        return: ObjectListPage JSON block containing a list of QuizReadData blocks.
    '''

    def get_quizzes(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/quizzes/".format(course_id=course_id)
        return self.__process_api_json("get_quizzes", url)

    '''
        Pulls information about a quiz attempt for a specific quiz, queried by the quiz_id.
        
        quiz_id (number) the id of the quiz

        return: ObjectListPage JSON block containing a list of QuizAttemptData blocks.
    '''
    
    def get_quiz_attempts(self, course_id, quiz_id):
        url = self._API_URL_PREFIX + "le/1.45/{course_id}/quizzes/{quiz_id}/attempts/".format(course_id=course_id, quiz_id=quiz_id)
        return self.__process_api_json("get_quiz_attempts", url)
  

    '''
        Retrieves all dropbox folders for an org unit. Each dropbox folder provides a place for
        org unit entities (users or groups of users) to submit work for assessment. Each dropbox folder
        represents a single opportunity for assessment(submission of a single paper for grading, quiz for testing, etc.)

        course_id: the orgUnitID, the ID of the course that the user is enrolled in.

        return: JSON array of DropboxFolder blocks.
    '''
    
    def get_dropbox_folders_for_org_unit(self, course_id):
        url = self._API_URL_PREFIX + "le/1.41/{course_id}/dropbox/folders/".format(course_id=course_id)
        return self.__process_api_json("get_dropbox_folders_for_org_unit", url) 
    
    '''
        Retrieves all submissions for a specific dropbox folder. 
        
        course_id: ID of the course that the user is enrolled in.
        folder_id: Folder ID for a specific dropbox folder

        return: JSON array of EntityDropbox structures that fully enumerates all
        submissions currently provided to the dropbox folders by all the entities.
    '''
    def get_submissions_for_dropbox_folder(self, course_id, folder_id):
        url = self._API_URL_PREFIX + "le/1.41/{course_id}/dropbox/folders/{folder_id}/submissions/?activeOnly=true".format(course_id=course_id,folder_id=folder_id)
        return self.__process_api_json("get_submissions_for_dropbox_folder", url)
    
    '''
        Retrieves all users enrolled in the specified org unit. 
        
        course_id: ID of the course that the user is enrolled in.

        return: JSON array of ClasslistUser data blocks.
    '''
    def get_enrolled_users_for_org_unit(self, course_id):
        url = self._API_URL_PREFIX + "le/1.41/{course_id}/classlist/".format(course_id=course_id)
        return self.__process_api_json("get_enrolled_users_for_org_unit", url)

    '''
        Pulls the number of scheduled items with a list of given course_ids and start_date and end_date. 

        course_ids: the list of course_ids
        start_date: start_date for time range to query
        end_date: end_date for time range to query

        return: ObjectListPage JSON block containing a list of ScheduledItem blocks. 
    '''
    def get_scheduled_item_counts(self, course_ids, start_date, end_date):
        url = self._API_URL_PREFIX + "le/1.41/content/myItems/due/itemCounts/?startDateTime={start_date}&endDateTime={end_date}&orgUnitIdsCSV=".\
            format(start_date=start_date, end_date=end_date)
        #test for if course_ids is a single-entry list. or null. 
        for index in range(len(course_ids)-1):
            url += course_ids[index]
            url += ","
        
        url += course_ids[len(course_ids)-1]

        return self.__process_api_json("get_scheduled_item_counts", url)



    '''
        This gets the numeric points and percentage grade of a course.
        
        course_id (str / int): the id of the course
        returns: tuple (fraction_string, percentage_string)
    '''

    def get_grade(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/grades/final/values/myGradeValue".format(
                course_id=course_id)

        grade_object = self.__process_api_json("get_grade", url)

        # TODO : Should do error checking on if these values are even in the json
        numerator = ""
        denominator = ""
        percentage_string = ""
        try:
            if grade_object["PointsNumerator"] is not None:
                numerator = grade_object["PointsNumerator"]
                num = int(numerator)
            if grade_object["PointsDenominator"] is not None:
                denominator = grade_object["PointsDenominator"]
                den = int(denominator)
            fraction_string = "{numerator}/{denominator}".format(numerator=numerator, denominator=denominator)

            if grade_object["DisplayedGrade"] is not None:
                percentage_string = grade_object["DisplayedGrade"]
        except TypeError:
            return "", ""

        percentage = num/den
        percentage = percentage * 100
        return fraction_string, percentage

    '''
        This retrieves all the assignments in gradebook for a particular course for the current logged in user,
        regardless if the grade of the assignment is 0 or empty
        
        course_id (str/int): the id of the course
        returns: array of grade_object_ids or -1 if no grades
    '''
    def get_all_assignments_in_gradebook(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/grades/".format(course_id=course_id)
        grade_objects = self.__process_api_json("get_all_graded_assignments_in_gradebook", url)
        # print(grade_objects)

        # No graded assignments in course
        if grade_objects is None:
            return [-1]

        g_obj_ids = []
        for g_obj in grade_objects:
            g_obj_ids.append(g_obj['Id'])

        # print(g_obj_ids)
        return g_obj_ids

    '''
        This gets the assignment name and percentage grade of a specific assignment.
        
        course_id (str/int): the id of the course
        grade_object_id (str/int): the id the of specific assignment
        returns: tuple (grade_object_id, course_id, assignment_name, percentage_string)
    '''
    def get_grade_of_assignment(self, course_id, grade_object_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/grades/{grade_object_id}/values/myGradeValue".format(
            course_id=course_id, grade_object_id=grade_object_id
        )
        # returns a dict with assignment info or 'None' if assignment has no grade yet
        grade_object = self.__process_api_json("get_grade_of_assignment", url)
        # print(grade_object)
        if grade_object is None:
            return grade_object_id, course_id, -1, -1

        assignment_name = grade_object["GradeObjectName"]
        percentage_string = grade_object["DisplayedGrade"]

        return grade_object_id, course_id, assignment_name, percentage_string

    '''
        This gets a file and saves it to a given destination 
        
        course_id (str / int): the id of the course
        topic_id (str / int): the id of the topic

        returns: a requests.response object containing a file
    '''
    def get_file_from_request(self, course_id, topic_id):
        # formatting downloadable link
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/content/topics/{topic_id}/file" \
                .format(course_id=course_id,
                        topic_id=topic_id)
        # Making the request to retrieve the file
        return self.__process_api_file("get_file_from_request", url)

    '''
        Get all topics for a given course.
        
        course_id (str / int): the id of the course
        returns: a TableOfContents JSON block, in a dictionary. 
    '''

    def get_topics(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/content/toc".format(course_id=course_id)
        return self.__process_api_json("get_topics", url)

    def get_forums(self, course_id):
        url = "https://purdue.brightspace.com/d2l/api/le/1.38/{course_id}/discussions/forums/" \
                .format(course_id=course_id)
        return self.__process_api_json("get_forums", url)

    def get_discussion_topics(self, course_id, forum_id):
        url = "https://purdue.brightspace.com/d2l/api/le/1.38/{course_id}/discussions/forums/{forum_id}/topics/" \
                .format(course_id=course_id,
                        forum_id=forum_id)
        return self.__process_api_json("get_disscussion_topics", url)

    def get_discussion_posts(self, course_id, forum_id, topic_id):
        url = "https://purdue.brightspace.com/d2l/api/le/1.38/{course_id}/discussions/forums/{forum_id}/topics/{topic_id}/posts/" \
                .format(course_id=course_id, forum_id=forum_id, topic_id=topic_id)
        return self.__process_api_json("get_dicussion_posts", url)

    '''
        Pulls all announcements from BrightSpace with a given course id.
        Announcements posted after "since" are returned. If no since is provided, 
        all announcements for this class are returned.
        "since" is a date in UTC+0 time, in the format of yyyy-MM-ddTHH:mm:ss.fffZ 

        course_id (str / int): the id of the course
        since (str): announcements before this time won't be returned. 
        return: a JSON array of NewsItem
    '''

    def get_class_announcements(self, course_id, since=None):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/news/".format(course_id=course_id)
        since = "since=" + since if since else ""
        url += "?" + since if since else ""

        return self.__process_api_json("get_news_class", url)

    '''
        Gets calender events from a class. The events that happen between startDateTime
        and endDateTime are returned.
        If an eventType is provided, only events of the specific type is returned.
        
        list of event types:
            Reminder(1), AvailabilityStarts(2), AvailabilityEnds(3)
            UnlockStarts(4), UnlockEnds(5), DueDate(6)

        returns: An ObjectListPage JSON block containing a list of EventDataInfo JSON data blocks.
    '''

    def get_calender_events(self, course_id, startDateTime, endDateTime, eventType=None):
        url = self._API_URL_PREFIX
        url += "le/1.38/{course_id}/calendar/events/myEvents/".format(course_id=course_id)
        url += "?"
        url += "eventType={eventType}&".format(eventType=eventType) if eventType else ""
        url += "startDateTime={sDate}&endDateTime={eDate}".format(sDate=startDateTime, eDate=endDateTime)

        return self.__process_api_json("get_calender_events", url)

    '''
        Retrieve all the calendar events for the calling user. within the provided course id
        
        course_id (str/int): a string of numbers representing the course
        
        returns: This action returns a JSON array of EventDataInfo data blocks.
    '''

    def get_course_all_events(self, course_id):
        url = self._API_URL_PREFIX
        url += "le/1.38/{course_id}/calendar/events/".format(course_id=course_id)

        return self.__process_api_json("get_course_all_events", url)

    '''
        Retrieve not submitted grade conditions 
        
        return. This action returns a ConditionsData JSON structure representing the conditions on the target
    '''

    def get_content_conditions(self):
        return

    '''
        Processing an api call that returns a json.
        
        call_name: The name of the functionality that is being processed. 
                    Used for debugging.
        api_url:   The url for the api call
        
        return: a json dictionary. See references for more informtion.
    '''
    def __process_api_json(self, call_name, api_url):
        res = self.__process_api(call_name, api_url)
        return res.json() if res else None

    '''
        Processing an api call that returns a file.
        
        call_name: The name of the functionality that is being processed. 
                    Used for debugging.
        api_url:   The url for the api call
        
        return: a file. See references for more informtion.
    '''
    def __process_api_file(self, call_name, api_url):
        res = self.__process_api(call_name, api_url)
        return res

    '''
        A general process for processing an api call.
        
        call_name: The name of the functionality that is being processed. 
                    Used for debugging.
        api_url:   The url for the api call
        
        return: the response from api call, could be many things. 
    '''

    def __process_api(self, call_name, api_url):
        if not self._session:
            if self._debug:
                print(call_name, ": Warning: Current session is Null. None is returned.")
            return None

        res = self._session.get(api_url, headers=self._HEADER)

        if self._debug:
            print(call_name, ": response status code: ", res.status_code)

        if res.status_code == 200:
            return res
        return None

    ''' ---------- Utilities & others ----------- '''

    '''
    Used for turning debug mode on / off
    
    debug (bool) : False for off, True for on.
    '''

    def set_debug_mode(self, debug):
        self._debug = debug

    # Modification of 'get_grade_of_assignment' to return just the overall points received
    def get_grade_received(self, course_id, grade_object_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/grades/{grade_object_id}/values/myGradeValue".format(
            course_id=course_id, grade_object_id=grade_object_id
        )
        # returns a dict with assignment info or 'None' if assignment has no grade yet
        grade_object = self.__process_api_json("get_grade_of_assignment", url)
        # print(grade_object)
        if grade_object is None:
            # meaning no points yet
            return 0, 0

        total = grade_object["PointsDenominator"]
        grade_received = grade_object["PointsNumerator"]

        return grade_received, total

    def get_upcoming_assignments(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/dropbox/folders/".format(course_id=course_id)
        upcoming = self.__process_api_json("get_upcoming_assignments", url)
        #file = open("/Users/raveena/Library/Preferences/PyCharmCE2019.2/scratches/scratch.json")
        #upcoming = json.load(file)
        print(upcoming)
        if upcoming is None:
            return []
        due = []
        for assignment in upcoming:
            if assignment["DueDate"] is None:
                l = [assignment["Name"], None]
            else:
                l = [assignment["Name"], assignment["DueDate"]]
            due.append(l)
        return due

    def get_past_assignments(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/dropbox/folders/".format(course_id=course_id)
        assignments = self.__process_api_json("get_past_assignments", url)
        # print(assignments)
        if assignments is None:
            return []
        past_assignments = []
        for assignment in assignments:
            attachment_len = len(assignment['Attachments'])
            attachment_file = None
            if attachment_len > 0:
                attachment_file = assignment['Attachments'][0]['FileName']
                # print(attachment_file)

            if assignment["DueDate"] is None:
                l = {'assignment_name': assignment["Name"], 'due_date': None, 'file_name': attachment_file}
            else:
                l = {'assignment_name': assignment["Name"], 'due_date': assignment["DueDate"], 'file_name': attachment_file}

            current_date = datetime.datetime.utcnow()
            assignment_due_date = datetime.datetime.fromisoformat(assignment['DueDate'][:-1])

            # # for testing
            # if attachment_file is not None and attachment_file == 'Question and Answer Plan.docx':
            #     assignment_due_date = datetime.datetime.now() + datetime.timedelta(days=1)

            diff = (assignment_due_date - current_date).days
            if diff < 0:
                past_assignments.append(l)
        return past_assignments





