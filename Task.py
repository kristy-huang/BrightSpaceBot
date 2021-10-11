import requests
from lxml import etree
from datetime import datetime

HEADER = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }

# Returns a requests.session that is logged in to brightspace
# with the given username and password.
# Needs to pass Duo Authentication manually - through their app.
#
# TODO: automate Duo Authentication
#
# username (str) - brightspace username.
# password (str) - <4-digit pin>,push  <4-digit pin>,<temp code> 
#                   ... whatever you use to login
# return: requests.session

def get_brightspace_session(username, password):
    session = requests.session()
    session = __login_purdue_cas(session, username=username, password=password)
    session = __login_brightspace(session)
    return session
    

# Returns a requests.session that is logged in to Purdue cas authentication.
#
# session (requests.session) - a new session.
# username (str) - brightspace username.
# password (str) - <4-digit pin>,push  <4-digit pin>,<temp code> 
#                   ... whatever you use to login
#
# return: requests.session

def __login_purdue_cas(session, username, password):

    res = session.get("https://www.purdue.edu/apps/account/cas/login", headers=HEADER)

    # Aborts if the request returns error codes - e.g. 4xx. 5xx.
    res.raise_for_status() 

    tree = etree.HTML(res.text)
    lt = tree.xpath('//*[@name="lt"]/@value')[0]

    cas_data = {
                "username": username,
                "password": password,
                "lt": lt,
                "execution": "e1s1",
                "_eventId": "submit",
                "submit": "Login",
            }

    res = session.post("https://www.purdue.edu/apps/account/cas/login", 
        data=cas_data, headers=HEADER)
    #print(res.status_code, res.text, res.cookies)

    res.raise_for_status()
    
    return session

# Returns a requests.session that is logged in to BrightSpace.
#
# session (requests.session) - a session logged in to Purdue cas.
# return: requests.session

def __login_brightspace(session):
    res = session.get("https://purdue.brightspace.com/d2l/lp/auth/saml/initiate-login?entityId=https://idp.purdue.edu/idp/shibboleth")
    res.raise_for_status()

    tree = etree.HTML(res.text)
    try:
        res = session.post(
            tree.xpath("//form/@action")[0],
            data={"SAMLResponse": tree.xpath('//input[@name="SAMLResponse"]/@value')[0]},
            headers=HEADER
        )
    except:
        print("Login failed. Please check your cridentials. ")

    return session

  
  
class Task:
  def__init__(self):
    #constructor for Task class
    self.session = get_brightspace_session("xxxx", "xxxx,push");
    #set necessary variables here. 
    
  
  def getTask():
    return self
  
  def determineTask():     
   #for now, all tasks are requests.  
   return Request(self)

class Request(Task):
  def __init__(self):
    #constructor for Request class
    #set necessary variables/fields here
  
  def getUpcomingAssignments():
    #return all upcoming assignments. 
    #figure out what datatype to return this as. 
    
  def getUpcomingQuizzes():
    #return all of user's upcoming quizzes across all classes.
    #figure out what dataype to return this as - list? 
    #makes BS API calls.  
    enrollments_url = "https://purdue.brightspace.com/d2l/api/lp/{version}/enrollments/myenrollments/".format(version=BP_VERSION)
    #print("enrollments url:", enrollments_url)
    res = self.session.get(enrollments_url, headers=HEADER)
    courses = res.json()["Items"]
    results = []
    for course in courses:
        quiz_url = "https://purdue.brightspace.com/d2l/api/le/{version}/{course_id}/quizzes/".format(version=BP_VERSION,
                                                                                                 course_id=course)
        #print("q url:", quiz_url)
        res = session.get(quiz_url, headers=HEADER)
        quizzes = res.json()["Objects"]
            #retrieving quizzes within a week. 
            for quiz in quizzes: 
                        #get today's date
                        current_date = datetime.now()
                        quiz_due_date = quiz.json()["DueDate"]
                        #find diff between quiz.due date and today
                        diff = quiz_due_date - current
                        #if diff less than or equal to 7 days = 604800 seconds
                        if diff <= 604800
                                    #add to results array
                                    results.append(quiz)
                        
     return results
            
      
  def getUpcomingExams(session):
    #return all of user's upcoming exams across all classes. 
            
  def suggestFocusTime():
    #return the top 3 weeks that have the most assignments
    #bot must go across all classes and calculate which weeks have the most assignments
    #this way, user can plan out what to focus on. 
    #makes BS API calls. 
   
  def getCurrentGrade():
    #return user's current grade in a specific class - class is passed as param
    #makes BS API call
   
  def getFeedback():
    
  def findStudent():
    
  def suggestStudyGroup():
    #searches through classlists of all user's courses, and finds other students that have courses in common
    #compiles these students with common courses and suggests this group as a potential study group to user. 
    
class Notification(Task):
  def __init__(self):
    #constructor for Notification subclass
    #set necessary variables/fields here
  
class Automation(Task):
  def __init__(self):
    #constructor for Automation subclass
    #set necessary variables/fields here
