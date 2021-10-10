from authentication import get_brightspace_session

import requests


class BSAPI():
    # ---------- Some initialization functions ---------------

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
       

    # ---------- Actual API call functions! ---------------
    # All functions in the section returns None if the current session is None, or 
    # there is an error (e.g. 404 not found) when trying to retrieve the data.
    # All functions returns a dictionary. Please see the reference pages for more
    # information.


    # Pulls user "who am i" information.
    #
    # returns: WhoAmIUser JSON

    def get_user_info(self):
        url = self._API_URL_PREFIX + "lp/1.21/users/"
        return self.__process_api("get_user_info", url)


    def get_enrollments(self):
        url = self._API_URL_PREFIX + "lp/1.26/enrollments/myenrollments/"
        return self.__process_api("get_enrollments", url)


    # Pulls all quiz information from BrightSpace with a given course id.
    #
    # course_id (str / int): the id of the course
    # return: ObjectListPage JSON block containing a list of QuizReadData blocks.

    def get_quizzes(self, course_id):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/quizzes/".format(course_id=course_id)
        return self.__process_api("get_quizzes", url)


    # Pulls all announcements from BrightSpace with a given course id.
    # Announcements posted after "since" are returned. If no since is provided, 
    # all announcements for this class are returned.
    # "since" is a date in UTC+0 time, in the format of yyyy-MM-ddTHH:mm:ss.fffZ 
    #
    # course_id (str / int): the id of the course
    # since (str): announcements before this time won't be returned. 
    # return: a JSON array of NewsItem

    def get_announcements_class(self, course_id, since=None):
        url = self._API_URL_PREFIX + "le/1.38/{course_id}/news/".format(course_id=course_id)
        since = "since=" + since if since else ""
        url += "?" + since if since else ""

        return self.__process_api("get_news_class", url)
        

    # A general process for processing an api call.
    #
    # call_name: The name of the functionality that is being processed. 
    #            Used for debugging.
    # api_url:   The url for the api call
    #
    # return: a json file. See references for more informtion. 

    def __process_api(self, call_name, api_url):
        if not self._session:
            if self._debug:
                print(call_name, ": Warning: Current session is Null. None is returned.")
            return None

        res = self._session.get(api_url, headers=self._HEADER)

        if self._debug:
            print(call_name, ": response status code: ", res.status_code)

        if res.status_code == 200:
            return res.json()
        return None

    # ---------- Utilities & others ---------------

    # Used for turning debug mode on / off
    #
    # debug (bool) : False for off, True for on.

    def set_debug_mode(self, debug):
        self._debug = debug

