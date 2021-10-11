import requests
from lxml import etree

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

