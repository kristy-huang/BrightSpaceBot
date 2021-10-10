import requests
from lxml import etree

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
    quiz_url = "https://purdue.brightspace.com/d2l/api/le/{version}/{course_id}/quizzes/".format(version=BP_VERSION, course_id=course_id)
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


def download__file(session):
    url = "https://purdue.brightspace.com/d2l/api/le/1.38/335757/content/toc"
    print("q url:", url)
    res = session.get(url, headers=HEADER, allow_redirects=True)

    print(res.status_code)
    topic = res.json()["Modules"][0]["Modules"]
    #[1]["Topics"]
    s = len(topic)
    for i in range(s):
        m = topic[i]["Topics"]
        for j in range(len(m)):
            print(m[j]["Url"])
    #open('facebook.pdf', 'wb').write(res.content)


def main():
    session = get_brightspace_session("xxxx", "xxxx,push")
    #quiz = get_quizzes(session, "335578")
    #get_grade(session, "335578")
    download__file(session)


if __name__ == "__main__":
    # res = requests.get("https://purdue.brightspace.com/d2l/api/le/1.38/{course_id}/quizzes/".format(course_id=335578))
    # print(res.status_code)
    print("---------------------------------")
    main()
