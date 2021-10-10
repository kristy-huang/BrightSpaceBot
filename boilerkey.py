import requests
from lxml import etree
import os
from pathlib import Path
from File import File
from datetime import datetime

HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
}

BP_VERSION = "1.38"
WHO_AM_I_VERSION = "1.0"


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
    session = login_purdue_cas(session, username=username, password=password)
    session = login_brightspace(session)
    return session


# Returns a requests.session that is logged in to Purdue cas authentication.
#
# session (requests.session) - a new session.
# username (str) - brightspace username.
# password (str) - <4-digit pin>,push  <4-digit pin>,<temp code>
#                   ... whatever you use to login
#
# return: requests.session

def login_purdue_cas(session, username, password):
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
    # print(res.status_code, res.text, res.cookies)

    res.raise_for_status()

    return session


# Returns a requests.session that is logged in to BrightSpace.
#
# session (requests.session) - a session logged in to Purdue cas.
# return: requests.session

def login_brightspace(session):
    res = session.get(
        "https://purdue.brightspace.com/d2l/lp/auth/saml/initiate-login?entityId=https://idp.purdue.edu/idp/shibboleth")
    res.raise_for_status()

    tree = etree.HTML(res.text)
    res = session.post(
        tree.xpath("//form/@action")[0],
        data={"SAMLResponse": tree.xpath('//input[@name="SAMLResponse"]/@value')[0]},
        headers=HEADER
    )

    return session


# Testing function to test if we actually logged in to BS!
# Prints names and end dates of all quizzes posted for given course
#
# session (requests.session): A session logged in to BS
# course_id (str): the id of the course
# return: None

def get_quizzes(session, course_id):
    quiz_url = "https://purdue.brightspace.com/d2l/api/le/{version}/{course_id}/quizzes/".format(version=BP_VERSION,
                                                                                                 course_id=course_id)
    print("q url:", quiz_url)
    res = session.get(quiz_url, headers=HEADER)

    quizzes = res.json()["Objects"]
    for quiz in quizzes:
        print(quiz["Name"], "  ", quiz["EndDate"])


# This gets the numeric points and percentage grade of a course
def get_grade(session, course_id):
    # surrounding request with try catch to capture any errors through
    try:
        grade_url = "https://purdue.brightspace.com/d2l/api/le/{version}/{course_id}/grades/final/values/myGradeValue".format(
            version=BP_VERSION, course_id=course_id)
        print(grade_url)
        res = session.get(grade_url, headers=HEADER)
        res.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        return

    grade_object = res.json()

    # TODO : Should do error checking on if these values are even in the json
    numerator = grade_object["PointsNumerator"]
    denominator = grade_object["PointsDenominator"]
    fraction_string = "{numerator}/{denominator}".format(numerator=numerator, denominator=denominator)
    percentage_string = grade_object["DisplayedGrade"]

    return fraction_string, percentage_string


def get_file_from_request(session, courseid, topicid, filename):
    # formatting downloadable link
    download_url = "https://purdue.brightspace.com/d2l/api/le/{version}/{course_id}/content/topic/{topic_id}/file" \
        .format(version=BP_VERSION,
                course_id=courseid,
                topic_id=topicid)
    # Making the request to retrieve the file
    res = session.get(download_url, headers=HEADER, allow_redirects=True)
    # saving that file internally
    open(filename, 'wb').write(res.content)
    # moving the file to a default location (testing location locally)
    source = filename
    destination = "/Users/raveena/Desktop/testing" + "/" + source  # for debugging (change later)
    os.rename(source, destination)


def download__file(session, courseid):
    url = "https://purdue.brightspace.com/d2l/api/le/1.38/{course_id}/content/toc".format(course_id=courseid)
    print("q url:", url)
    res = session.get(url, headers=HEADER)

    print("Download files request code: " + str(res.status_code))
    # saving the json returned
    modules = res.json()["Modules"]

    print(len(modules))  # DEBUG: number of big sections

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
                    file = File(m_topics[k]["Title"], m_topics[k]["Url"])
                    filename = file.fileTitle + ".pdf"
                    get_file_from_request(session, courseid, m_topics[k]["TopicId"], filename)


def get_discussion_topics(session, courseID, forumID):
    topic_url = "https://purdue.brightspace.com/d2l/api/le/{verison}/{course_id}/discussions/forums/{forum_id}/topics/" \
        .format(verison=BP_VERSION,
                course_id=courseID,
                forum_id=forumID)
    res = session.get(topic_url, headers=HEADER)
    topics = res.json()
    return topics


def get_discussion_due_dates(session, courseID):
    dates = []
    current_date = datetime.now()  # saving the current date
    print(current_date)

    discussion_url = "https://purdue.brightspace.com/d2l/api/le/{version}/{course_id}/discussions/forums/" \
        .format(version=BP_VERSION,
                course_id=courseID)
    res = session.get(discussion_url, headers=HEADER)

    threads = res.json()
    for thread in threads:
        print(thread["Name"])
        print("----")
        # get the list of topics for each thread
        topics = get_discussion_topics(session, courseID, thread["ForumId"])
        for t in topics:
            print(t["Name"])
            # if its null, then we don't need the value
            if t["EndDate"] is not None:
                dates.append(t["EndDate"])
    return dates


def main():
    session = get_brightspace_session("xxxx", "xxxx,push")
    # quiz = get_quizzes(session, "xxxx")
    # get_grade(session, "xxxx")
    # download__file(session, "xxxxx")
    dates = get_discussion_due_dates(session, "xxxx")
    print(dates)


if __name__ == "__main__":
    print("---------------------------------")
    main()
    # example: the code below will be used to see the difference in days between now and due date
    current_date = datetime.now()  # saving the current date
    print(current_date)
    end = datetime(2021, 10, 13)
    print(end - current_date)
