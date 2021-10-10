from bs_api import BSAPI

import datetime


class BSUtilities():
    def __init__(self):
        self._bsapi = BSAPI()

    # Same as set_session in BSAPI

    def set_session(self, session):
        self._bsapi.set_session(session)
 

    def set_session(self, username, password):
        self._bsapi.set_session(username, password)


    '''
        Replaces the BSAPI() object with a new one.
        bsapi: instance of BSAPI()
    '''
    def replace_bsapi(self, bsapi):
        self._bsapi = bsapi
    

    '''
        Pulls all announcements from every class the user is currently enrolled in.
        If a parameter "since" is given, only announcements having start times after 
        this time will be returned.
        
        since (str) : representing a time with timezone UTC+0, in the format 
        (optional)   of yyyy-MM-ddTHH:mm:ss.fffZ, zero padded. 
                    e.g. 2046-05-20T13:15:30.067Z

        returns: an array of dictionaries, representing announcements in the format of:
                {'course_id': str,
                'Title': str,
                'Text': str,
                'StartDate': datetime
         }
    '''
    def get_announcements(self, since=None):
        try:
            if isinstance(since, str):
                since = datetime.datetime.strptime(since, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return False
        
        classes_list = self.get_classes_enrolled()
        all_announcements = []
        for c in classes_list.keys():
            class_announces = self._bsapi.get_class_announcements(classes_list[c])
            for announce in class_announces:
                startDate = datetime.datetime.strptime(announce['StartDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
                if not since or self.__timestamp_later_than(since, startDate) <= 0:
                    announce_dict = {
                        'course_id': classes_list[c],
                        'Title': announce['Title'],
                        'Text': announce['Body']['Text'],
                        'StartDate': startDate
                    }
                    all_announcements.append(announce_dict)
        return all_announcements
        #sorted(ann, key = lambda i: i['StartDate'], reverse=True)
        #sorted(ann, key = lambda i: i['course_id'], reverse=True)


    '''
        Pulls all events from currently enrolled classe that happened between 
        startDateTime and endDateTime. 
        If no dates are provided, events from the past 1 year time window will
        be returned.
        If only one of start / end date is provided, a 1 year time window will 
        be calculated based on the provided date.

        
        startDateTime (str): representing a time with timezone UTC+0, in the format 
                            of yyyy-MM-ddTHH:mm:ss.fffZ, zero padded. 
                            e.g. 2046-05-20T13:15:30.067Z
        endDateTime (str): same as startDateTime

        returns: an array of dictionaries, representing events in the format of:
                {'course_id': str,
                'Title': str,
                'Description': str,
                'StartDate': datetime
                }
    '''
    def get_all_events(self, startDateTime=None, endDateTime=None):
        if not startDateTime and not endDateTime:
            endDateTime = datetime.datetime.utcnow()
            startDateTime = endDateTime - datetime.timedelta(days = 365) 
            endDateTime = endDateTime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            startDateTime = startDateTime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        elif not startDateTime:
            try:
                datetime_start = datetime.datetime.strptime(startDateTime, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                print("startDateTime format incorrect.")
                return None
        
            endDateTime = datetime_start + datetime.timedelta(days = 365) 
            endDateTime = endDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        elif not endDateTime:
            try:
                datetime_end = datetime.datetime.strptime(endDateTime, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                print("endDateTime format incorrect.")
                return None

            startDateTime = datetime_end - datetime.timedelta(days = 365) 
            startDateTime = startDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        events = []
        classes_list = self.get_classes_enrolled()
        for c in classes_list.keys():
            cal_events = self._bsapi.get_calender_events(classes_list[c], startDateTime, endDateTime)
            cal_events = cal_events['Objects']
            for cal_event in cal_events:
                startDate = datetime.datetime.strptime(cal_event['StartDateTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
                events.append({'course_id': cal_event['OrgUnitId'],
                               'Title': cal_event['Title'],
                               'Description': cal_event['Description'],
                               'StartDate': startDate})

        return events


    '''
        Gets a list of classes the user is currently enrolled in.
        Returns a dictionary in the format of 
        {classname1: course_id1,
        classname2: course_id2}

        return: dict
    '''
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


    '''
        Returns True if time_str is later than (or at the same time as) the current time
        or the time_str is None (which means infinitly later in the future!)
        Return False otherwise (or when there is an error).
        time_str (str): representing a time with timezone UTC+0, in the format 
                        of yyyy-MM-ddTHH:mm:ss.fffZ, zero padded. 
                        e.g. 2046-05-20T13:15:30.067Z
    '''
    def __timestamp_later_than_current(self, time_str):

        if not isinstance(time_str, str):
            return True

        try:
            reference_time = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return False

        now = datetime.datetime.utcnow()

        return self.__timestamp_later_than(reference_time, now) >= 0


    '''
        Returns 1 if time1 is later than the time2.
        Returns 0 if time1 is equal the time2.
        Returns -1 if time1 is earlier than the time2.
        Returns -2 if there is an error.
    
        time1, time2 (datetime objects): represent times with timezone UTC+0
    '''
    def __timestamp_later_than(self, time1, time2):
        if time1 > time2:
            return 1
        if time1 < time2:
            return -1
        if time1 == time2:
            return 0