from authentication import get_brightspace_session

import requests
import os


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


    def set_session(self, session):
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
        url = self._API_URL_PREFIX + "lp/1.21/users/"
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
        This gets the numeric points and percentage grade of a course.
        
        course_id (str / int): the id of the course
        returns: tuple (fraction_string, percentage_string)
    ''' 
    def get_grade(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/grades/final/values/myGradeValue".format(
                course_id=course_id)

        grade_object = self.__process_api_json("get_grade", url)

        # TODO : Should do error checking on if these values are even in the json
        numerator = grade_object["PointsNumerator"]
        denominator = grade_object["PointsDenominator"]
        fraction_string = "{numerator}/{denominator}".format(numerator=numerator, denominator=denominator)
        percentage_string = grade_object["DisplayedGrade"]

        return fraction_string, percentage_string


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

