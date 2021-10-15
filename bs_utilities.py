import json
from bs_api import BSAPI

import datetime
import urllib.parse
import os
from pathlib import Path


class BSUtilities():
    def __init__(self, debug=False):
        self._bsapi = BSAPI(debug=debug)
        self._debug = debug

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
        Downloads one file from a topic with a given course id and topic id.

        course_id (int / str): id of the course
        topic_id (int / str): id of the topic
        destination (str): location the files are downloaded.
    '''
    def download_file(self, course_id, topic_id, destination):
        res = self._bsapi.get_file_from_request(course_id, topic_id)
        
        filename = res.headers['Content-Disposition']
        filename = filename[:filename.rindex("\"")]
        filename = filename[filename.rindex("\"") + 1: ]
        filename = urllib.parse.unquote(filename)

        destination += "/" if destination[-1] != '/' else ""
        if not os.path.exists(destination):
            os.makedirs(destination)
        full_path = destination + filename

        open(full_path, 'wb').write(res.content)
        if self._debug:
            print("File {filename}: downloaded.".format(filename=filename))


    '''
        Downloads all files for a course recursively.

        course_id (int / str): id of the course
        destination (str): location the files are downloaded.
    '''
    # TODO: files not located in a sub-module are not downloaded.
    def download_files(self, course_id, destination):
    
        modules = self._bsapi.get_topics(course_id)["Modules"]

        if self._debug:
            print("number of big sections:", len(modules))

        # going through the big sections
        for i in range(len(modules)):
            # go through any folders the module section may have (module inside module)
            for j in range(len(modules[i]["Modules"])):
                m_topics = modules[i]["Modules"][j]["Topics"]
                # going through the topics to see files listed
                for k in range(len(m_topics)):
                    # getting the type of file it is
                    suffix = Path(m_topics[k]["Url"]).suffixes
                    extension = suffix[len(suffix) - 1]
                    # currently only saving pdf files
                    if extension == ".pdf":
                        self.download_file(course_id, m_topics[k]["TopicId"], destination=destination)


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
        Get the discussion due dates of a given course.

        course_id (int / str): id of the course
        returns: an array of dates(str).
    '''
    def get_discussion_due_dates(self, course_id):
        dates = []

        threads = self._bsapi.get_forums(course_id)
        if not threads:
            return dates

        for thread in threads:
            # get the list of topics for each thread
            topics = self._bsapi.get_discussion_topics(course_id, thread["ForumId"])
            for t in topics:
                # if its null, then we don't need the value
                if t["EndDate"] is not None:
                    dates.append(t["EndDate"])
        return dates

    '''
        This functions pulls up a student's upcoming quizzes across all their

        enrolled classes. By "upcoming", we mean within the next week. Serves user story 6 from Sprint 1. 
        
        returns: list of QuizReadDate blocks.
    '''
    def get_upcoming_quizzes(self):
        enrolled_courses = self.get_classes_enrolled()
        upcoming_quizzes = {}
        for course in enrolled_courses: 
            result = self._bsapi.get_quizzes(enrolled_courses[course])        #returns a list of QuizReadData blocks - dictionaries
            quizzes = result['Objects']
            for quiz in quizzes:       #for each block in the list,
                #get today's date
                current_date = datetime.datetime.utcnow()
                if quiz['DueDate'] is not None:
                    quiz_due_date = datetime.datetime.strptime(quiz['DueDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
                #find diff between quiz.due date and today
                    diff = quiz_due_date - current_date
                #if diff less than or equal to 7 days = 604800 seconds
                #for 2 weeks = 1209600 seconds
                    diff_in_seconds = diff.total_seconds()
                    if diff_in_seconds <= 1209600 and diff_in_seconds > 0:
                        #this is an upcoming quiz within the next week/2 weeks
                        #print('found quiz within a week')       #debug statement
                        course_name = course
                        upcoming_quizzes[course_name] = quiz
                        #upcoming_quizzes['name'] = course_name
                        #quiz_due_date_local_time = self.datetime_from_utc_to_local(quiz['DueDate'])
                        #quiz['DueDate'] = quiz_due_date_local_time
        return upcoming_quizzes
    
    #sub-function of suggest_focus_time(), maybe need this idk. May delete.
    def find_end_term_date(self):
        ORG_ID_CLASS = 3
        ORG_ID_GROUP = 4

        enrolled_classes = {}
        end_term_date = datetime.datetime.now()
        enroll = self._bsapi.get_enrollments()
        for item in enroll['Items']:
            if item['OrgUnit']['Type']['Id'] == ORG_ID_CLASS:
                # Check if the class ended already
                end_date = item['Access']['EndDate']
                if self.__timestamp_later_than(end_date, end_term_date):
                    end_term_date = end_date
                
        return end_term_date


    '''
       This function calculates the total number of assignments across all courses for each week, from now until

       the end of the semester. Finally, the top 3 weeks with the most assignments are reported back to the user. 
       
       Serves user story 9 in Sprint 1. 

       Returns:  

    '''

    def suggest_focus_time(self):
        enrolled_courses = self.get_classes_enrolled()
        current_date = datetime.now()
        end_date = current_date + datetime.timedelta(days = 7)
        item_counts = self._bsapi.get_scheduled_item_counts(enrolled_courses.values(), current_date, end_date)

        


        future_scheduled_items = []
        #for each course, grab all the scheduled items. 
        for course_id in enrolled_courses.values():
            course_items = self._bsapi.get_scheduled(course_id)
            for item in course_items:
                due_date = item.json()["DueDate"]
                if due_date:
                    if self.__timestamp_later_than_current(due_date):
                        future_scheduled_items.append(item)
        #we now have all future scheduled_items. 
            


        end_term_date = self.find_end_term_date()
        return
        #return busiest_weeks


    '''
        Pulls events of a specific type from currently enrolled classes that  
        happened between startDateTime and endDateTime. 
        If no dates are provided, events from the past 1 year time window will
        be returned.
        If only one of start / end date is provided, a 1 year time window will 
        be calculated based on the provided date.
        If no eventType is provided, Reminders(1) will be returned.

        list of event types:
            Reminder(1), AvailabilityStarts(2), AvailabilityEnds(3)
            UnlockStarts(4), UnlockEnds(5), DueDate(6)
        
        startDateTime (str): representing a time with timezone UTC+0, in the format 
                            of yyyy-MM-ddTHH:mm:ss.fffZ, zero padded. 
                            e.g. 2046-05-20T13:15:30.067Z
        endDateTime (str): same as startDateTime
        eventType (int / str): represents a event type.

        returns: an array of dictionaries, representing events in the format of:
                {'course_id': str,
                'Title': str,
                'EventType': str,
                'Description': str,
                'StartDate': datetime
                }
    '''
    def get_events_by_type(self, startDateTime=None, endDateTime=None, eventType=1):
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

        if isinstance(eventType, str):
            if eventType == "Reminder":
                eventType = 1
            elif eventType == "AvailabilityStarts":
                eventType = 2
            elif eventType == "AvailabilityEnds":
                eventType = 3
            elif eventType == "UnlockStarts":
                eventType = 4
            elif eventType == "UnlockEnds":
                eventType = 5
            elif eventType == "DueDate":
                eventType = 6
        
        events = []
        classes_list = self.get_classes_enrolled()
        for c in classes_list.keys():
            cal_events = self._bsapi.get_calender_events(classes_list[c], startDateTime, endDateTime, eventType=eventType)
            cal_events = cal_events['Objects']
            for cal_event in cal_events:
                startDate = datetime.datetime.strptime(cal_event['StartDateTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
                events.append({'course_id': cal_event['OrgUnitId'],
                               'Title': cal_event['Title'],
                               'Description': cal_event['Description'],
                               'StartDate': startDate})

        return events


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

    def get_letter_grade(self, percentage):
        if percentage >= 90:
            return 'A'
        elif 80 <= percentage < 90:
            return 'B'
        elif 70 <= percentage < 80:
            return 'C'
        elif 60 <= percentage < 50:
            return 'D'
        else:
            return 'F'