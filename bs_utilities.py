from bs_api_calls import BSAPI

import datetime

class BSUtilities():
    def __init__(self):
        self._bsapi = BSAPI()

    # Same as set_session in BSAPI
    
    def set_session(self, session):
        self._bsapi.set_session(session)
 

    def set_session(self, username, password):
        self._bsapi.set_session(username, password)

    # Gets a list of classes the user is currently enrolled in.
    # Returns a dictionary in the format of 
    # {classname1: course_id1,
    #  classname2: course_id2}
    #
    # return: dict

    def get_classes_enrolled(self):
        ORG_ID_CLASS = 3
        ORG_ID_GROUP = 4

        enrolled_classes = {}

        enroll = self._bsapi.get_enrollments()
        for item in enroll['Items']:
            if item['OrgUnit']['Type']['Id'] == ORG_ID_CLASS:
                # Check if the class ended already
                end_date = item['Access']['EndDate']
                if self.__timestamp_later_than_current(end_date):
                    class_name = item['OrgUnit']['Name']
                    class_id = item['OrgUnit']['Id']
                    enrolled_classes[class_name] = class_id
                
        return enrolled_classes

    # Returns True if time_str is later than (or at the same time as) the current time.
    # Return False otherwise (& when None is passed in).
    #
    # time_str: a string representing a time with timezone UTC+0, in the format 
    #           of yyyy-MM-ddTHH:mm:ss.fffZ, zero padded. 
    #           e.g. 2046-05-20T13:15:30.067Z


    def __timestamp_later_than_current(self, time_str):

        if not isinstance(time_str, str):
            return True

        reference_time = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        now = datetime.datetime.utcnow()

        return self.__timestamp_later_than(reference_time, now) >= 0


    # Returns 1 if time1 is later than the time2.
    # Returns 0 if time1 is equal the time2.
    # Returns -1 if time1 is earlier than the time2.
    #
    # time1 : strings representing times with timezone UTC+0, in the format 
    # time2   of yyyy-MM-ddTHH:mm:ss.fffZ, zero padded. 
    #         e.g. 2046-05-20T13:15:30.067Z

    def __timestamp_later_than(self, time1, time2):
        if time1 > time2:
            return 1
        if time1 < time2:
            return -1
        if time1 == time2:
            return 0