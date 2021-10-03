class Task:
  def__init__(self):
    #constructor for Task class
    #set necessary variables here. 
  
  def getTask():
    return self
  
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
