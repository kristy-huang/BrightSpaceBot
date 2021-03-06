from bs_api import BSAPI
from database.db_utilities import DBUtilities
from database.mysql_database import MySQLDatabase
from rename_file import RenameFile

import datetime
import shutil
import urllib.parse
import os
from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from File import File, StorageTypes
from rename_file import RenameFile
import json


class BSUtilities():
    def __init__(self, debug=False):
        self._bsapi = BSAPI(debug=debug)
        self._debug = debug
        self.drive = None

    # Logs in to BS automatically
    #
    # dbu (DBUtilities object): a DBUtilities object connected to a database
    # discord_username (str): discord username

    def set_session_auto(self, dbu, discord_username):
        self._bsapi.set_session_auto(dbu, discord_username)

    # Same as set_session in BSAPI
    def set_session_by_session(self, session):
        self._bsapi.set_session_by_session(session)

    def set_session(self, username, password):
        self._bsapi.set_session(username, password)

    def session_exists(self):
        return self._bsapi._session != None

    def check_connection(self):
        if not self.session_exists():
            return False

        a = self._bsapi.get_user_info()

        return True if a else False

    '''
        Replaces the BSAPI() object with a new one.
        bsapi: instance of BSAPI()
    '''

    def init_google_auths(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
        drive = GoogleDrive(gauth)
        self.drive = drive


    def replace_bsapi(self, bsapi):
        self._bsapi = bsapi

    '''
        Downloads one file from a topic with a given course id and topic id.

        course_id (int / str): id of the course
        topic_id (int / str): id of the topic
        destination (str): location the files are downloaded.
    '''


    def check_for_folder(self, storage_type, course_name):
        if storage_type == "Local Machine":
            return 0

    def download_file(self, course_id, topic_id, destination, type, drive, course_name):
        res = self._bsapi.get_file_from_request(course_id, topic_id)

        filename = res.headers['Content-Disposition']
        filename = filename[:filename.rindex("\"")]
        filename = filename[filename.rindex("\"") + 1:]
        filename = urllib.parse.unquote(filename)

        if type.startswith('Local'):
            # First check if a folder exists with course name
            path = os.path.join(destination, course_name)

            os.makedirs(path, exist_ok=True)
            destination = path
            destination += "/" if destination[-1] != '/' else ""
            if not os.path.exists(destination):
                os.makedirs(destination)
            full_path = destination + filename
            # saving the path in the right place
            
            with open(full_path, 'wb') as file:
                file.write(res.content)
            if self._debug:
                print("File {filename}: downloaded.".format(filename=filename))
        else:
            # TODO download to google drive
            return_val = self.validate_path_drive(destination, self.drive)

            os.makedirs("./temp/", exist_ok=True)
            temp_path = os.path.join("./temp/", filename)

            with open(temp_path, 'wb') as file:
                file.write(res.content)

            # for debugging, just using this default file
            try:
                self.upload_to_google_drive(self.drive, destination, temp_path, course_name)
            except Exception as e:
                print(e)
                print("Google upload failed.")



    def upload_to_google_drive(self, drive, storage_path, file, course_name):
        file_to_upload = file
        # finding the folder to upload to
        folders = self.get_all_files_in_google(drive)
        rename = RenameFile()
        folder_id = -1
        found = False
        course_folder_id = -1

        filename = file.split('/')[-1]

        for folder in folders:
            if folder.fileTitle == storage_path:
                folder_id = folder.filePath
        #print(folder_id)
        if folder_id == -1:
            # upload it to the root (My Drive)
            gd_file = drive.CreateFile({'title': filename})
        else:
            subfolders = rename.get_folders_from_specified_folder(drive, folder_id, [])
            for s in subfolders:
                if s['title'] == course_name:
                    found = True
                    course_folder_id = s['id']
                    break
            # currently takes the folder id from browser of url for the folder they want to upload something in
            if found == False:
                # course folder does not exist so create one
                folder = drive.CreateFile({'title': course_name,
                                  'mimeType': 'application/vnd.google-apps.folder',
                                  'parents': [{'id': folder_id}]})
                folder.Upload()
                course_folder_id = folder['id']

            gd_file = drive.CreateFile({'title': filename,
                                        'parents': [{'id': course_folder_id}]})


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
        t: Google drive or Local
    '''

    # TODO: files not located in a sub-module are not downloaded.

    def download_files(self, course_id, destination, t, course_name, file_types=None):

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
                    if len(suffix) == 0:
                        continue
                    extension = suffix[len(suffix) - 1]
                    # currently only saving pdf files

                    print(Path(m_topics[k]["Url"]).suffixes)
                    try:
                        if file_types  == "pdf" and extension == ".pdf":
                            self.download_file(course_id, m_topics[k]["TopicId"], destination=destination,
                                type=t, course_name=course_name)
                        elif file_types == "videos" and extension.lower() in ["mp4", "avi", "wmv"]:
                            self.download_file(course_id, m_topics[k]["TopicId"], destination=destination,
                                type=t, course_name=course_name)
                        elif file_types == "slides" and extension.lower() in ["pptx", "ppt"]:
                            self.download_file(course_id, m_topics[k]["TopicId"], destination=destination,
                                type=t, course_name=course_name)
                        elif extension in [".pdf", ".mp4", ".avi", ".wmv", ".pptx", ".ppt", ".html", '.xlsx']:
                            self.download_file(course_id, m_topics[k]["TopicId"], destination=destination,
                                                type=t, course_name=course_name)
                    except Exception as e:
                        print(e)
            
        # If files are uploaded to google drive, cleanup the temp storage location
        if not t.startswith('Local'):
            shutil.rmtree("./temp/")

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
                        'Title': announce['Title'].replace("\r\n", "\n").replace("\xa0", " "),
                        'Text': announce['Body']['Text'].replace("\r\n", "\n"),
                        'StartDate': startDate
                    }
                    all_announcements.append(announce_dict)
        return all_announcements
        # sorted(ann, key = lambda i: i['StartDate'], reverse=True)
        # sorted(ann, key = lambda i: i['course_id'], reverse=True)

    '''
        Get the discussion due dates of a given course.

        course_id (int / str): id of the course
        returns: an array of dates(str).
    '''

    def get_discussion_due_dates_TEST(self):
        file = open("/Users/raveena/Library/Preferences/PyCharmCE2019.2/scratches/scratch2.json")
        topics = json.load(file)
        dates = []
        for t in topics:
            arr = []
            arr.append(t["Name"])
            arr.append(t["EndDate"])
            dates.append(arr)
        return dates

    def get_discussion_due_dates(self, course_id):
        dates = []
        threads = self._bsapi.get_forums(course_id)

        if not threads:
            return dates

        for thread in threads:
            # get the list of topics for each thread
            topics = self._bsapi.get_discussion_topics(course_id, thread["ForumId"])
            for t in topics:
                arr = []
                arr.append(t["Name"])
                arr.append(t["EndDate"])
                dates.append(arr)
        return dates

    '''
        This is a subfunction for get_assignment_feedback. It finds the courseID/orgUnitID 

        for an inputted course_name. We need this ID for future API calls. 

        returns: int course_ID, or None if the inputted course_name is not a valid course that the user is enrolled in. 

    '''

    def find_course_ID(self, course_name_str):
        # course_name_str = str(course_name.content)
        enrolled_courses = self.get_classes_enrolled()
        for course in enrolled_courses:
            class_name = str(course)
            if class_name.__contains__(course_name_str.upper()):
                return enrolled_courses[course]

        return None

    '''
        This is a subfunction that finds the folderID of the specific dropbox folder we need to access the feedback on an assignment
        
        dropbox_folders: JSON array of DropboxFolder blocks.

        Returns: int folder_ID, or None if the inputted assignment_name is not a valid assignment in this course. 
    '''

    def get_folder_ID_from_dropbox(self, dropbox_folders, assignment_name):
        assignment_name_str = str(assignment_name)

        for folder in dropbox_folders:
            folder_name = folder['Name']
            folder_name_str = str(folder_name)
            if folder_name_str.__contains__(assignment_name_str):
                folder_ID = folder['Id']
                return folder_ID

        return None

    '''
        This is a helper function for get_assignment_feedback(). 
    '''

    def get_feedback(self, submissions_arr):
        entity_dropbox = submissions_arr[0]
        feedback_block = entity_dropbox["Feedback"]
        if feedback_block is not None:
            feedback = feedback_block["Feedback"]
            if feedback is not None:
                feedback_text = feedback["Text"]
                return feedback_text

        return None

    '''
        Function that suggest study groups. The user can specify how many students to have in their group, as well as 
        how many courses they want to have in common with the students in their study group. 

        returns: a list of students to comprise the group.
    '''
    def suggest_study_groups(self, num_of_students_str, num_of_courses_str):
        output_dict = self.suggest_study_groups_num_of_courses(num_of_courses_str)
        return output_dict
    
    '''
        This is a subfunction for suggest_study_groups(). This particular function is for when only the "number of students"
        parameter has been specified. The "number of courses to have in common" parameter has not been given. 

        returns: a dictionary of students (key) and the number of courses in common (value)
    '''
    def suggest_study_groups_num_of_students(self, num_of_students_str):
        sorted_dict = self.suggest_study_groups_no_parameters()
        #num_of_students = int(num_of_students_str)
        
        return sorted_dict

    '''
        This is a subfunction for suggest_study_groups(). This particular function is for when only the "number of courses"
        parameter has been specified. The "number of students" parameter has not been given. 

        returns: a dictionary of students (key) and the number of courses in common (value)
    '''
    def suggest_study_groups_num_of_courses(self, num_of_courses_str):
        sorted_dict = self.suggest_study_groups_no_parameters()
        num_of_courses = int(num_of_courses_str)
        output_dict = {}
        for student in sorted_dict:
            if sorted_dict[student] == num_of_courses:
                output_dict[student] = num_of_courses
        
        return output_dict
    
    '''
        This is a subfunction for suggest_study_groups(). This particular function is for when no parameters have been given.
        The user has not specified how many students to have in their group, nor have they specified how many courses they 
        want to have in common with the students in their study group.

        returns: a dictionary of students (key) and the number of courses in common (value)
    '''
    def suggest_study_groups_no_parameters(self):
        temp_dict = {}
        enrolled_courses = self.get_classes_enrolled_2()
        x = 0
        for course in enrolled_courses:
            if x == 0:
                #add names from classlist 1 to the dict
                classlist_user_blocks = self._bsapi.get_enrolled_users_for_org_unit(enrolled_courses[course])
                for classlist_user in classlist_user_blocks:
                    first_name = classlist_user["FirstName"]
                    last_name = classlist_user["LastName"]
                    current_name = first_name + " " + last_name
                    temp_dict[current_name] = 1        
                x = -1
            else:
                classlist_user_blocks = self._bsapi.get_enrolled_users_for_org_unit(enrolled_courses[course])
                for classlist_user in classlist_user_blocks:
                    first_name = classlist_user["FirstName"]
                    last_name = classlist_user["LastName"]
                    current_name = first_name + " " + last_name
                    if current_name in temp_dict:
                        temp_dict[current_name] += 1
                    else:
                        temp_dict[current_name] = 1
        
        sorted_dict =  dict(sorted(temp_dict.items(), key = lambda x: x[1], reverse = True))
        return sorted_dict

    def get_classes_enrolled_2(self):
        ORG_ID_CLASS = 3
        ORG_ID_GROUP = 4

        enrolled_classes = {}

        enroll = self._bsapi.get_enrollments()
        for item in enroll['Items']:
            if item['OrgUnit']['Type']['Id'] == ORG_ID_CLASS:
                # Check if the class ended already
                end_date = item['Access']['EndDate']
                #name = item['OrgUnit']['Name']
                class_name = item['OrgUnit']['Name']
                substring = "Fall 2021"
                if self.__timestamp_later_than_current(end_date) and substring in class_name:
                    #class_name = item['OrgUnit']['Name']
                    #print(class_name)
                    class_id = item['OrgUnit']['Id']
                    enrolled_classes[class_name] = class_id

        return enrolled_classes
    
    
    '''
        Experimenting with the table of contents format. 
    '''
    def toc_experiment(self):
        course_ID = self.find_course_ID("CS 307")
        #print(course_ID)
        toc_block_modules = self._bsapi.get_topics(course_ID)["Modules"]
        
        # going through the big sections
        for i in range(len(toc_block_modules)):
            # go through any folders the module section may have (module inside module)
            for j in range(len(toc_block_modules[i]["Modules"])):
                m_topics = toc_block_modules[i]["Modules"][j]["Topics"]
                # going through the topics to see files listed
                for k in range(len(m_topics)):
                    # getting the type of file it is
                    url = m_topics[k]["Url"]
                    title = m_topics[k]["Title"]
                    #topic_id = m_topics[k]["TopicId"]
                    
                    if ("quickLink") in url:
                        print("Title: " + title)
                        #url = m_topics[k]["Url"]
                        print("URL: " + url)
                    '''else:
                        print("quickLink not found")
                        print("Title: " + title)
                        print("URL: " + url)'''

        return
    
    
    '''
        This is a function that checks if a given assignemnt in a course has feedback or not. This reuses much of the code
        from the get_assignment_feedback() function below this function.

        returns: String of feedback, or NULL if there is no feedback, or error message if parameters are incorrect. 
    '''
    def check_for_assignment_feedback(self, course_name_str, assignment_name_str):
        output = self.get_assignment_feedback(course_name_str, assignment_name_str)
        return output
    
    '''
        This is a function that grabs feedback (if it exists) for an assignment in a course. 

        returns: String of feedback, or NULL if there is no feedback, or error message if parameters are incorrect. 
    '''

    def get_assignment_feedback(self, course_name_str, assignment_name_str):
        course_ID = self.find_course_ID(course_name_str)
        if course_ID is not None:
            dropbox_folders = self._bsapi.get_dropbox_folders_for_org_unit(course_ID)
            folder_ID = self.get_folder_ID_from_dropbox(dropbox_folders, assignment_name_str)
            if folder_ID is not None:
                submissions_arr = self._bsapi.get_submissions_for_dropbox_folder(course_ID,
                                                                                 folder_ID)  # JSON array of EntityDropbox structures
                if submissions_arr is not None:
                    feedback = self.get_feedback(submissions_arr)
                    if feedback is not None:
                        return feedback
                    else:
                        output = "BOT REPORT: No feedback has been provided for this assignment."
                else:
                    output = "BOT REPORT: I do not have permission to access these submissions."
            else:
                output = "ERROR: Please make sure the assignment you have specified is spelled correctly and exists."
                return output

        else:
            output = "ERROR: Please make sure the course you have specified is spelled correctly and is a course that you are currently enrolled in."
        return output

    '''
        This function tries to search for an inputted student name in a given class.  
        
        returns: True or False. True if the student is listed in the list of users for a class, or False otherwise.
    '''

    def search_for_student_in_class(self, course_name_str, student_name_str):
        course_ID = self.find_course_ID(course_name_str)
        if course_ID is not None:
            classlist_user_blocks = self._bsapi.get_enrolled_users_for_org_unit(course_ID)
            for classlist_user in classlist_user_blocks:
                first_name = classlist_user["FirstName"]
                last_name = classlist_user["LastName"]
                current_name = first_name + " " + last_name
                if current_name.lower() == student_name_str.lower():
                    return True

        return False

    '''
        This is a helper function for get_upcoming_quizzes(). It is used to determine whether a given 

        quiz has been attempted or not. Returns true if it is unattempted, or false it has been been attempted.  
        
        returns: True or False.
    '''

    def isQuizUnattempted(self, course_id, quiz_id):
        result = self._bsapi.get_quiz_attempts(course_id, quiz_id)  # returns a list of QuizAttemptData blocks.
        if result is not None:
            return False

        return True

    '''
        This functions pulls up a student's upcoming quizzes across all their

        enrolled classes. By "upcoming", we mean within the next week. Serves user story 6 from Sprint 1. 
        
        returns: list of QuizReadDate blocks.
    '''

    def get_upcoming_quizzes(self):
        enrolled_courses = self.get_classes_enrolled()
        upcoming_quizzes = {}
        for course in enrolled_courses:
            result = self._bsapi.get_quizzes(
                enrolled_courses[course])  # returns a list of QuizReadData blocks - dictionaries
            quizzes = result['Objects']
            for quiz in quizzes:  # for each block in the list,
                # get today's date
                current_date = datetime.datetime.utcnow()

                if quiz['DueDate'] is not None:
                    quiz_due_date = datetime.datetime.strptime(quiz['DueDate'], "%Y-%m-%dT%H:%M:%S.%fZ")

                    # find diff between quiz.due date and today
                    diff = quiz_due_date - current_date
                    # if diff less than or equal to 7 days = 604800 seconds
                    # for 2 weeks = 1209600 seconds
                    diff_in_seconds = diff.total_seconds()
                    if diff_in_seconds <= 604800 and diff_in_seconds > 0:
                        # if the quiz isUnattempted, we can add it to our output array.
                        if self.isQuizUnattempted(enrolled_courses[course], quiz):
                            course_name = course
                            upcoming_quizzes[course_name] = quiz
        return upcoming_quizzes

    # sub-function of suggest_focus_time(), maybe need this idk. May delete.
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
        end_date = current_date + datetime.timedelta(days=7)
        item_counts = self._bsapi.get_scheduled_item_counts(enrolled_courses.values(), current_date, end_date)

        future_scheduled_items = []
        # for each course, grab all the scheduled items.
        for course_id in enrolled_courses.values():
            course_items = self._bsapi.get_scheduled(course_id)
            for item in course_items:
                due_date = item.json()["DueDate"]
                if due_date:
                    if self.__timestamp_later_than_current(due_date):
                        future_scheduled_items.append(item)
        # we now have all future scheduled_items.

        end_term_date = self.find_end_term_date()
        return
        # return busiest_weeks

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
            startDateTime = endDateTime - datetime.timedelta(days=365)
            endDateTime = endDateTime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            startDateTime = startDateTime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        elif not startDateTime:
            try:
                datetime_start = datetime.datetime.strptime(startDateTime, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                print("startDateTime format incorrect.")
                return None

            endDateTime = datetime_start + datetime.timedelta(days=365)
            endDateTime = endDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        elif not endDateTime:
            try:
                datetime_end = datetime.datetime.strptime(endDateTime, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                print("endDateTime format incorrect.")
                return None

            startDateTime = datetime_end - datetime.timedelta(days=365)
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
            cal_events = self._bsapi.get_calender_events(classes_list[c], startDateTime, endDateTime,
                                                         eventType=eventType)
            cal_events = cal_events['Objects']
            for cal_event in cal_events:
                startDate = datetime.datetime.strptime(cal_event['StartDateTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
                events.append({'course_id': cal_event['OrgUnitId'],
                               'Title': cal_event['Title'],
                               'EventType': eventType,
                               'Description': cal_event['Description'],
                               'StartDate': startDate})

        return events

    # returns a string describing the event
    def get_events_by_type_past_24h(self, eventType=1):
        endDateTime = datetime.datetime.utcnow()
        startDateTime = endDateTime - datetime.timedelta(days=10)
        endDateTime = endDateTime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        startDateTime = startDateTime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        events = self.get_events_by_type(startDateTime, endDateTime, eventType)
        str_rep = ""
        # print("events:", events)
        for event in events:
            # TODO: get a mapping from course id to course names from the database
            str_rep += "Class: {}\n".format(event['course_id'])
            str_rep += "{}\n\n".format(event['Title'])
            str_rep += "{}\n".format(event['Description'])
            str_rep += "-----------------------------------\n\n"

        return str_rep

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

    '''
        Retrieves any assignments that were recently graded
        
        returns an array with the grade and assignment details of recently graded assignments
        or if no assignments were recently graded, return empty array
    '''

    def get_grade_updates(self):
        sql = MySQLDatabase('database/db_config.py')
        sql.create_table('GRADED_ASSIGNMENTS', 'grade_object_id INT PRIMARY KEY, '
                                               'course_id INT,'
                                               'assignment_name VARCHAR(255), '
                                               'grade VARCHAR(255)')
        # print(sql.show_tables())
        enrolled_courses = self.get_classes_enrolled()
        # print(enrolled_courses)
        grades = []
        for course_id in enrolled_courses.values():
            # g_obj_ids is an array that contains the ids of all the graded assignments for a course
            g_obj_ids = self._bsapi.get_all_assignments_in_gradebook(course_id)
            if len(g_obj_ids) != 0 and g_obj_ids is not None and g_obj_ids[0] != -1:
                for g_obj_id in g_obj_ids:
                    assignment_and_grade = self._bsapi.get_grade_of_assignment(course_id, g_obj_id)
                    g_id = assignment_and_grade[0]
                    c_id = assignment_and_grade[1]
                    assignment_name = assignment_and_grade[2]
                    grade = assignment_and_grade[3]
                    # print(assignment_and_grade)
                    data = {
                        "grade_object_id": g_id,
                        "course_id": c_id,
                        "assignment_name": assignment_name,
                        "grade": grade
                    }
                    sql_response = sql.find_rows_one_attr('GRADED_ASSIGNMENTS', 'grade_object_id', g_id)
                    # if there is a grade for the assignment and that assignment is not in the db yet, insert into db
                    if grade != -1 and sql_response == -1:
                        sql.insert_into('GRADED_ASSIGNMENTS', data)
                        grades.append(data)

        return grades


    def get_dict_of_discussion_dates(self):
        classes = self.get_classes_enrolled()
        dates = {}
        for key, value in classes.items():
            dates[key] = self.get_discussion_due_dates(value)
        return dates

    # given end time (24 hrs or 2 weeks) give the list of upcoming dates
    def find_upcoming_disc_dates(self, add_days, discussion_dates):
        # The ending date to compare with
        ending_date = datetime.datetime.utcnow() + datetime.timedelta(days=add_days)
        print(ending_date)
        string = ""
        for discussion in discussion_dates:
            if discussion[0] is not None and discussion[1] is not None:
                name = discussion[0]
                date = datetime.datetime.fromisoformat(discussion[1][:-1])
                diff = date - ending_date
                print(diff)
                # Checking if the post is due in less than 24 hrs
                if add_days == 1:
                    if diff.days == 0 or diff.days == -1:
                        string = string + name + " Discussion Post is due in 24 hours.\n"
                # if there is a post due in a week
                elif add_days == 7:
                    if -7 <= diff.days <= 0:
                        string = string + name + " Discussion Post is due in a week.\n"
                # find the next 2 weeks
                elif add_days == 14:
                    if -14 <= diff.days <= 0:
                        string = string + name + " Discussion Post is due in two weeks.\n"
                # Just want all discussion posts upcoming
                elif add_days == -1:
                    if diff.days >= 0:
                        string = string + name + " is upcoming\n"

        return string


    def find_course_id(self, class_name):
        dictionary = self.get_classes_enrolled()

        class_name = class_name.replace(' ', '')
        course_id = -1
        for key, value in dictionary.items():
            if key.lower().find(class_name.lower()) != -1:
                course_id = value

        return course_id

    def find_course_id_and_fullname(self, class_name):
        dictionary = self.get_classes_enrolled()

        class_name = class_name.replace(' ', '')
        course_id = -1
        for c_full_name, c_id in dictionary.items():
            c_full_name = c_full_name.replace(' ', '')
            if c_full_name.lower().find(class_name.lower()) != -1:
                return c_full_name, c_id
        return (None, None)

    # Since our project is in "testing" phase, you have to manually add test users until you publish the app
    # My personal email is the only test user now, but we can add more
    def init_google_auths(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
        self.drive = GoogleDrive(gauth)

    def get_all_files_in_google(self, drive):
        # only querying files (everything) from the 'MyDrive' root
        fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        #print(fileList)
        # Use this to save all the folders in 'MyDrive'
        folderList = []
        for file in fileList:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                myFile = File(file['title'], file['id'])
                myFile.storageType = StorageTypes.GOOGLE_DRIVE
                folderList.append(myFile)
        #print(folderList)
        return folderList

    def get_notifications_past_24h(self):
        utc_one_day_before = datetime.datetime.utcnow() - datetime.timedelta(days=10)
        utc_one_day_before = utc_one_day_before.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        announcements = self.get_announcements(since=utc_one_day_before)
        # announcements = self.get_announcements()

        notification_header = "Announcements from the past 24 hours: \n\n"
        notification = ""
        for announcement in announcements:
            # TODO: get a mapping from course id to course names from the database
            notification += "Class: {}\n".format(announcement['course_id'])
            notification += "{}\n\n".format(announcement['Title'])
            notification += "{}\n".format(announcement['Text'])
            notification += "-----------------------------------\n\n"
        return notification_header + notification if notification else ""

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

    # Algorithm to get overall points received in a class if not displayed at top
    def sum_total_points(self, courseID):
        gradeIDs = self._bsapi.get_all_assignments_in_gradebook(courseID)
        #print(gradeIDs)
        yourTotal = 0
        classTotal = 0
        for id in gradeIDs:
            yourGrade, total = self._bsapi.get_grade_received(courseID, id)
            print(str(total) + " " + str(yourGrade))
            yourTotal = yourTotal + yourGrade
            classTotal = classTotal + total

        return yourTotal, classTotal

    def process_upcoming_dates(self, upcoming_list):
        due = []
        current_utc = datetime.datetime.utcnow()
        for assignment in upcoming_list:
            date = assignment[1]
            if date is not None:
                date = datetime.datetime.fromisoformat(date[:-1])
                diff = date - current_utc
                if diff.days >= 0:
                    due.append(assignment)
        return due
        # print(diff.days)

    '''
        This functions pulls up all of a student's upcoming quizzes across all their

        enrolled classes. 

        returns: list of QuizReadDate blocks.
    '''

    def get_all_upcoming_quizzes(self):
        enrolled_courses = self.get_classes_enrolled()
        # print(enrolled_courses)
        upcoming_quizzes = []
        for course_name, course_id in enrolled_courses.items():
            result = self._bsapi.get_quizzes(course_id)  # returns a list of QuizReadData blocks - dictionaries
            quizzes = result['Objects']
            for quiz in quizzes:  # for each block in the list,
                # get today's date
                current_date = datetime.datetime.utcnow()

                if quiz['DueDate'] is not None:
                    quiz_due_date = datetime.datetime.fromisoformat(quiz['DueDate'][:-1])
                    # print(quiz_due_date)

                    # find diff between quiz due date and today
                    diff = (quiz_due_date - current_date).days
                    # print(diff)
                    # for upcoming quizzes due today or later in the future: diff >= 0
                    if diff >= 0:
                        data = {
                            "course_id": course_id,
                            "course_name": course_name,
                            "quiz_name": quiz['Name'],
                            "due_date": quiz['DueDate']
                        }
                        # print(data)
                        upcoming_quizzes.append(data)
        return upcoming_quizzes

    def get_sorted_grades(self):
        # list of courses in preferred priority
        course_priority = []

        # list of missing grade courses that cannot be prioritize with the bot's function
        missing_grade_courses = []

        # getting user enrolled classes
        user_classes = self.get_current_semester_courses()

        # arrays needed for sorting courses
        # class_names will store all course names of the user
        # grades_frac will store all the fraction grade of the user for those courses
        class_names = []
        grades_frac = []

        # revised for loop
        for name, course_id in user_classes.items():
            # getting class names and fraction grade from the enrolled class list
            class_names.append(name)
            grade_string = self._bsapi.get_grade(course_id)[0]
            fraction_grade = 0.0

            if not grade_string == '':
                fraction_grade = float(grade_string[0]) / float(grade_string[1])

            grades_frac.append(fraction_grade)

        sorted_grade_frac = sorted(grades_frac)

        # appending sorted courses to course_priority
        for x in sorted_grade_frac:
            if not x == 0:
                course_priority.append(class_names[grades_frac.index(x)])

        for x in class_names:
            if not x in course_priority:
                missing_grade_courses.append(x)

        # print(course_priority)

        return course_priority, missing_grade_courses

    def get_current_semester_courses(self):
        # new dictionary of courses for current semester
        current_enrolled_courses = {}

        # user enrolled courses
        # this might include courses that do not have end dates
        # for instance, training courses or supplemental instructions
        user_enrolled_course = self.get_classes_enrolled()

        # current_semester will either be Fall, Sprint, or Summer accordingly to the date
        current_semester = ""

        # pin point for getting current semester
        current_date = datetime.datetime.today()

        # get current month, day from current date
        current_month = current_date.month
        current_day = current_date.day

        # Fall semester always start at the 4th Monday[19-25] of August
        # Spring semester always start at January
        # Summer semester always start at June until first week of August
        if current_month == 8:
            if current_day <= 15:
                current_semester = "Summer"
            else:
                current_semester = "Fall"
        elif 9 <= current_month:
            current_semester = "Fall"
        elif 6 <= current_month:
            current_semester = "Summer"
        elif 1 <= current_month:
            current_semester = "Spring"

        current_semester += " "
        current_semester += current_date.strftime("%Y")

        for name, course_id in user_enrolled_course.items():
            if current_semester in name:
                current_enrolled_courses[name] = course_id

        return current_enrolled_courses

    def get_course_by_due_date(self):
        # list of dictionary of courses by earliest due dates
        course_priority = []

        # list of courses that do not have a corresponding event in the given interval
        event_missing_courses = []

        # getting enrolled classes
        user_classes = self.get_current_semester_courses()

        # general time case
        start_time = datetime.datetime.utcnow()
        end_time = start_time + datetime.timedelta(days=122)  # roughly 4 months

        # Finding events
        for course_name, course_id in user_classes.items():
            event_title = ""
            event_end_day = ""
            course_events = self._bsapi.get_course_all_events(course_id)
            for event in course_events:
                event_end_time = datetime.datetime.strptime(event["EndDateTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
                if event_end_time > start_time:
                    event_title = event["Title"]
                    event_end_day = event["EndDateTime"]
                    break
                elif event_end_time > end_time:
                    break
            if event_title != "":
                course_priority.append({'Course Name': course_name,
                                        'Course Id': course_id,
                                        'Event Name': event_title,
                                        'Due Date': event_end_day})
            else:
                event_missing_courses.append({'Course Name': course_name,
                                              'Course Id': course_id})

        # sorting part required
        course_priority = sorted(course_priority, key=lambda k: k['Due Date'])

        return course_priority, event_missing_courses

    def get_course_url(self):
        # url dictionary format: purdue.brightspace.com/d2l/home/{course_id}
        course_urls = {}

        # get user enrolled classes
        user_classes = self.get_current_semester_courses()

        for course_name, course_id in user_classes.items():
            course_home_page = "https://purdue.brightspace.com/d2l/home/{course_id}".format(course_id=course_id)
            course_urls[course_name] = course_home_page

        return course_urls

    # start_time and end_time will be used as date objects
    def get_upcoming_events(self, start_time, end_time):
        # list of dictionary of events
        event_list = []

        # setting time interval
        if start_time is None and end_time is None:
            # general time case
            start_time = datetime.datetime.utcnow()
            end_time = start_time + datetime.timedelta(days=122)  # roughly 4 months

        # get user enrolled classes
        user_classes = self.get_current_semester_courses()

        utc_offset = datetime.datetime.utcnow() - datetime.datetime.today()

        # find and add matching events within the given time interval
        for course_name, course_id in user_classes.items():
            course_events = self._bsapi.get_course_all_events(course_id)
            for event in course_events:
                event_end_time = datetime.datetime.strptime(event["EndDateTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
                event_end_time = event_end_time - utc_offset
                if start_time <= event_end_time <= end_time:
                    event_list.append({'Course Name': course_name,
                                       'Course Id': course_id,
                                       'Event Name': event["Title"],
                                       'Description': event["Description"],
                                       'Due Date': event_end_time.strftime("%m/%d/%y %H:%M")})

        # sorting before return
        event_list = sorted(event_list, key=lambda k: k['Due Date'])

        return event_list

    def get_focus_suggestion(self, user_requested_order):
        # list of suggestion for classes
        suggested_classes = []
        lack_info_classes = []

        # get user enrolled class for this semester
        user_classes = self.get_current_semester_courses()

        # courses sorted by grade
        user_sorted_grade = self.get_sorted_grades()[0]
        #print(user_sorted_grade)
        user_missing_grade = self.get_sorted_grades()[1]
        #print(user_missing_grade)

        # courses sorted by due dates
        user_sorted_due_dates = self.get_course_by_due_date()[0]
        #print(user_sorted_due_dates)
        user_missing_due_dates = self.get_course_by_due_date()[1]
        #print(user_missing_due_dates)

        # courses sorted by un-submitted assignments
        # needs implementation

        if user_requested_order == 1:  # grade, deadline
            # should start from lowest grades
            # but if there is no grade nor deadline the course should not be recommended
            # for course in user_sorted_grade:
            #    if course in user_sorted_due_dates:
            #        suggested_classes.append(course)

            suggested_classes = user_sorted_grade

            for course in user_missing_grade:
                if course not in suggested_classes and course in user_sorted_due_dates:
                    suggested_classes.append(course)

            for name, course_id in user_classes.items():
                if name not in suggested_classes:
                    lack_info_classes.append({'Course Name': name,
                                              'Lack': "Grade & Deadline"})

        elif user_requested_order == 2:  # deadline, grade
            # should start from earliest deadlines
            # but if there is no grade nor deadline the course should not be recommended
            for course in user_sorted_due_dates:
                suggested_classes.append(course['Course Name'])

            for course in user_missing_due_dates:
                if course not in suggested_classes and course in user_sorted_grade:
                    suggested_classes.append(course)

            for course in user_classes.items():
                if course not in suggested_classes:
                    lack_info_classes.append({'Course Name': course,
                                              'Lack': "Grade & Deadline"})

        return suggested_classes, lack_info_classes



    # checks if a specific topic is a kaltura lecture. Returns Trur / False for the result.
    #
    # course_id (int / str): which course the topic belongs to
    # topic_id (int / str): the id of the topic

    def check_kaltura(self, course_id, topic_id):
        TOPIC_TYPE_FILE = 1
        TOPIC_TYPE_LINK = 3

        topic_content = self._bsapi.get_topic_content(course_id, topic_id)
        if not topic_content:
            if self._debug:
                print("Check kaltura: topic does not exist")
            return False

        if topic_content["TopicType"] != TOPIC_TYPE_LINK:
            if self._debug:
                print("Check kaltura: topic is not a link")
            return False

        next_url = "https://purdue.brightspace.com" + topic_content["Url"]
        res = self._bsapi.just_gimme_a_response(next_url)
        if res.status_code != 200:
            if self._debug:
                print(f"Check kaltura: failed to acces link in the topic. status code: {res.status_code}")
            return False

        if "kaf.kaltura.com" in str(res.content):
            return True
        return False

    def get_students_who_posted(self, course_id, forum_id, topic_id):
        students = []
        posts = self._bsapi.get_discussion_posts(course_id=course_id, forum_id=forum_id, topic_id=topic_id)
        for post in posts:
            name = post['PostingUserDisplayName']
            name = name.lower()
            students.append(name)
        return students

    def get_all_forum_ids_names(self, course_id):
        forums = self._bsapi.get_forums(course_id)
        forum_ids_names = []
        for forum in forums:
            forum_ids_names.append({"id": forum['ForumId'], "name": forum['Name']})
        return forum_ids_names

    def get_all_topic_ids_names(self, course_id, forum_id):
        topics = self._bsapi.get_discussion_topics(course_id, forum_id)
        topic_ids_names = []
        for topic in topics:
            topic_ids_names.append({"id": topic['TopicId'], "name": topic['Name'], "due_date": topic['EndDate']})
        return topic_ids_names

    def get_updated_sections(self, username):
        sql = MySQLDatabase('database/db_config.py')
        sql.create_table('COURSE_SECTIONS', 'username VARCHAR(255),'
                                            'course_id VARCHAR(255),'
                                            'num_sections INT,'
                                            'sections VARCHAR(2048),'
                                            'PRIMARY KEY (username, course_id)')
        # course_id = 335093  # com 217
        # print(sql.show_tables())
        enrolled_courses = self.get_classes_enrolled()
        response = 'You have no new sections added.'
        for course_name, course_id in enrolled_courses.items():
            secs = []
            sections = self._bsapi.get_topics(course_id)
            if len(sections) != 0 and sections is not None:
                num_sections = len(sections['Modules'])
                for section in sections['Modules']:
                    sec_title = section['Title']
                    secs.append(sec_title)
                formatted_secs = self.format_sections(secs)
                print(formatted_secs)
                sql_response = sql.general_command(f"SELECT * FROM COURSE_SECTIONS "
                                                   f"WHERE username=\'{username}\' AND course_id=\'{course_id}\'")
                # if that section is not in the db yet, insert into db
                if len(sql_response) == 0:
                    sql.general_command(f"INSERT INTO COURSE_SECTIONS (username, course_id, num_sections, sections) "
                                        f"VALUES (\"{username}\", \"{course_id}\", \"{num_sections}\", \"{formatted_secs}\")")
                    response = f"{course_name} has {num_sections} new sections added. The following sections have been added by " \
                               f"your instructor: {formatted_secs} \n\n"
                else:
                    num_sec_in_db = sql_response[0][2]
                    if num_sections > num_sec_in_db:
                        diff = self.get_diff_in_list(sql_response[0][3], formatted_secs)
                        response = f"{course_name} has {num_sections - num_sec_in_db} new sections added. The following sections have been added by " \
                                   f"your instructor: {diff} \n\n"

        return response

    def format_sections(self, sections):
        result = ''
        for section in sections:
            result = result + "," + section
        return result[1:]

    def get_diff_in_list(self, original, new):
        og_arr = original.split(",")
        new_arr = new.split(",")
        result = []
        for n in new_arr:
            if n not in og_arr:
                result.append(n)
        return result

    '''Returns an array of the last modified dates in each section and topic'''
    def get_last_mod_from_sections(self, course_id):
        #modules = self._bsapi.get_topics(course_id)["Modules"]
        file = open("/Users/raveena/Library/Preferences/PyCharmCE2019.2/scratches/scratch3.json")
        modules = json.load(file)
        modules = modules["Modules"]


        if self._debug:
            print("number of big sections:", len(modules))

        last_mod_dates = []
        # going through the big sections
        for i in range(len(modules)):
            arr = []
            m = modules[i]["Title"]
            module_string = f"MODULE: {m}"
            arr.append(module_string)
            arr.append(modules[i]["LastModifiedDate"])
            # go through any folders the module section may have (module inside module)
            for j in range(len(modules[i]["Modules"])):
                m_topics = modules[i]["Modules"][j]["Topics"]
                t = modules[i]["Modules"][j]["Title"]
                topic_string = f"TOPIC: {t}"
                arr.append(topic_string)
                arr.append(modules[i]["Modules"][j]["LastModifiedDate"])
                # going through the topics to see files listed
                for k in range(len(m_topics)):
                    a = m_topics[k]["Title"]
                    assignment_string = f"FILE: {a}"
                    arr.append(assignment_string)
                    arr.append(m_topics[k]["LastModifiedDate"])

            last_mod_dates.append(arr)
        return last_mod_dates

