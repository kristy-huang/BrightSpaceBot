import json
from bs_api import BSAPI

import datetime
import urllib.parse
import os
from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from File import File, StorageTypes


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
    def download_file(self, course_id, topic_id, destination, type, drive):
        res = self._bsapi.get_file_from_request(course_id, topic_id)
        
        filename = res.headers['Content-Disposition']
        filename = filename[:filename.rindex("\"")]
        filename = filename[filename.rindex("\"") + 1: ]
        filename = urllib.parse.unquote(filename)
        print(filename)
        if type == 'LOCAL':
            destination += "/" if destination[-1] != '/' else ""
            if not os.path.exists(destination):
                os.makedirs(destination)
            full_path = destination + filename
            # saving the path in the right place
            open(full_path, 'wb').write(res.content)
            if self._debug:
                print("File {filename}: downloaded.".format(filename=filename))
        else:
            # TODO download to google drive
            return_val = self.validate_path_drive(destination, drive)
            open(filename, 'wb').write(res.content)
            # for debugging, just using this default file
            self.upload_to_google_drive(drive, destination, filename)
            os.remove(filename)

    def upload_to_google_drive(self, drive, storage_path, file):
        file_to_upload = file
        # finding the folder to upload to
        folders = self.get_all_files_in_google(drive)
        folder_id = -1
        for folder in folders:
            if folder.fileTitle == storage_path:
                folder_id = folder.filePath
                break
        print(folder_id)
        if folder_id == -1:
            # upload it to the root (My Drive)
            gd_file = drive.CreateFile({'title': file})
        else:
            # currently takes the folder id from browser of url for the folder they want to upload something in
            gd_file = drive.CreateFile({'parents': [{'id': folder_id}]})

        # Read file and set it as the content of this instance.
        gd_file.SetContentFile(file)
        # Upload the file
        gd_file.Upload()
        # handles memory leaks
        gd_file = None

    '''
        Downloads all files for a course recursively.

        course_id (int / str): id of the course
        destination (str): location the files are downloaded.
    '''
    # TODO: files not located in a sub-module are not downloaded.
    def download_files(self, course_id, destination, t):
    
        modules = self._bsapi.get_topics(course_id)["Modules"]
        if t != "LOCAL":
            drive = self.init_google_auths()

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
                        self.download_file(course_id, m_topics[k]["TopicId"], destination=destination, type=t, drive=drive)


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
                    string_rep = t["EndDate"]
                    mdy = string_rep.split(" ")[0].split("-")
                    end = datetime(int(mdy[0]), int(mdy[1]), int(mdy[2]))
                    # saving datetime objects
                    dates.append(end)
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

    def get_dict_of_discussion_dates(self):
        classes = self.get_classes_enrolled()
        dates = {}
        for key, value in classes.items():
            dates[key] = self.get_discussion_due_dates(value)
        return dates

    # given end time (24 hrs or 2 weeks) give the list of upcoming dates
    def find_upcoming_disc_dates(self, add_days, dates):
        current_date = datetime.datetime.now()  # saving the current date
        ending_date = datetime.datetime.today() + datetime.timedelta(days=add_days)
        string = ""
        for key, value in dates.items():
            for i in value:
                # less than 24 hours left
                if add_days == 1:
                    diff = i - current_date
                    if diff.days == 0 or diff.days == -1:
                        string = string + " " + key + ", due " + i.strftime("%d-%b-%Y") + "\n"
                elif add_days == 14:
                    diff = ending_date - i
                    if 0 <= diff.days <= 14:
                        string = string + " " + key + ", due " + i.strftime("%d-%b-%Y") + "\n"
                # just give everything upcoming
                else:
                    diff = i - current_date
                    if diff.days >= 0:
                        string = string + " " + key + ", due " + i.strftime("%d-%b-%Y") + "\n"

        return string

    def find_course_id(self, class_name):
        dictionary = self.get_classes_enrolled()
        course_id = -1
        for key, value in dictionary.items():
            if key.lower().find(class_name.lower()) != -1:
                course_id = value


        return course_id

    # Since our project is in "testing" phase, you have to manually add test users until you publish the app
    # My personal email is the only test user now, but we can add more
    def init_google_auths(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
        drive = GoogleDrive(gauth)
        return drive

    def get_all_files_in_google(self, drive):
        # only querying files (everything) from the 'MyDrive' root
        fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        # Use this to save all the folders in 'MyDrive'
        folderList = []
        for file in fileList:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                myFile = File(file['title'], file['id'])
                myFile.storageType = StorageTypes.GOOGLE_DRIVE
                folderList.append(myFile)

        return folderList

    # Algorithm to check if path is a valid path
    def validate_path_drive(self, storage_path, drive):
        # checks if inputted path is valid or not for their local machine
        if not os.path.exists(storage_path):
            # check if its a valid google drive folder in root (update later for nested folders)
            folderList = self.get_all_files_in_google(drive)
            for folder in folderList:
                if folder.fileTitle == storage_path:
                    return True
            else:
                return False
        return True
