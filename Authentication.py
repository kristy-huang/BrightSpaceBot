from typing import Counter
from database.db_utilities import DBUtilities
import requests
from lxml import etree
import pyotp
import base64

HEADER = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }

# Returns a requests.session that is logged in to brightspace
# with the given username and password.
# Needs to pass Duo Authentication manually - through their app.
#
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
    


# Accesses the database with the config file located at database_config.
# Pulls necessary data from the database and logs in the user to BrightSpace.
#
# dbu (DBUtilities object): a DBUtilities object connected to a database
# discord_username (str): discord username
# 
# return: requests.session


def get_brightspace_session_auto(dbu, discord_username):
    session = requests.session()

    db_res = dbu.get_bs_username_pin(discord_username)
    while not db_res:
        print("Please setup your account first. ")
        setup_automation(dbu, discord_username)
        db_res = dbu.get_bs_username_pin(discord_username)


    user_name = db_res[0][0]
    pin = db_res[0][1]
    pin = str(pin)
    while len(pin) < 4:
        pin = "0" + pin

    passcode = __get_password(dbu, discord_username)
    password = "{},{}".format(pin, passcode)
    #print(password)

    session = __login_purdue_cas(session, username=user_name, password=password)
    session = __login_brightspace(session)
    return session
    #setup_automation(discord_username, dbu)





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
    try:
        lt = tree.xpath('//*[@name="lt"]/@value')[0]
    except:
        print("Login failed. Please check your credentials.")
        return None


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
        return None

    return session


# Generates a duo authenticate password

def __get_password(dbu, user_name):
    s_c = dbu.get_hotp_secret_counter(user_name)
    if s_c:
        secret = s_c[0][0]
        counter = s_c[0][1]
        
    p = pyotp.HOTP(base64.b32encode(secret.encode()))
    curr_passcode = p.at(counter)
    dbu.increase_hotp_counter(user_name)
    return curr_passcode


def setup_automation(dbu, discord_username, bs_username, bs_pin, url):
    HOTP_HEADER = {"User-Agent": "okhttp/3.11.0"}

    def res_sanity_check(res):
        res_json = res.json()
        if "response" not in res_json:
            return "Unkown error: No response contained.", False

        if res_json["stat"] == 'FAIL' and res_json["code"] == 40403:
            return "Invalid activation code. Get a new one.", False
        
        return "Success", True
            

    if not bs_pin.isnumeric() or len(bs_pin) != 4:
        return "pin format error", False
    try:
        bs_pin = int(bs_pin)
    except:
        return "pin format error", False

    if not bs_username.isalnum():
        return "username format error", False

    '''url = input("enter url")
    bs_username = input("enter BrightSpace username")
    bs_pin = input("enter BrightSpace pin (4-digit number)")'''

    '''while True:
        try:
            bs_pin = int(bs_pin)
            break
        except:
            bs_pin = input("enter BrightSpace pin (4-digit number)")'''


    code = url.split('/')[-1]
    params = {
        "app_id": "com.duosecurity.duomobile.app.DMApplication",
        "app_version": "2.3.3",
        "app_build_number": "323206",
        "full_disk_encryption": False,
        "manufacturer": "Google",
        "model": "Pixel",
        "platform": "Android",
        "jailbroken": False,
        "version": "6.0",
        "language": "EN",
        "customer_protocol": 1,
    }

    activation_url = "https://api-1b9bef70.duosecurity.com/push/v2/activation/{}".format(code)
    res = requests.post(activation_url, headers=HOTP_HEADER, params=params)

    #print(activation_url)
    #print(res.json())
    sc = res_sanity_check(res)

    if not sc[1]:
        #print(sc[0])
        return sc

    res_data = res.json()["response"]
    hotp_secret = res_data["hotp_secret"]
    hotp_counter = 0
    
    dbu.add_hotp_secret_counter(discord_username, hotp_secret, hotp_counter)
    dbu.add_bs_username_pin(discord_username, bs_username, bs_pin)

    return "Success", True

