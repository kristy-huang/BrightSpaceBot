# Practicing alternative methods for accessing information through
# BrightSpace while we get authentication working
from selenium import webdriver
import os
import time

def testing_webdriver():
        # Basically, this controls all the movements automatically
        path = os.path.abspath(webdriver.__file__)
        driver = webdriver.Chrome("/Users/raveena/Downloads/chromedriver")

        # Getting logged in to brightspace (auto fills and clicks button)
        driver.get(
                "https://www.purdue.edu/apps/account/cas/login?service=https%3A%2F%2Fwww.purdue.edu%2Fapps%2Fidphs%2FAuthn%2FExtCas%3Fconversation%3De1s1&entityId=https%3A%2F%2Ff81993d1-f040-40db-88cd-dddba8664daf.tenants.brightspace.com%2FsamlLogin")
        username = "REPLACE WITH YOUR USERNAME"
        pin = "REPLACE WITH PIN"

        # Goes to one of my default BrightSpace pages and downloads syllabus
        driver.find_element_by_xpath("/html/body/div[1]/div[2]/form/fieldset/div[1]/input").send_keys(username)
        driver.find_element_by_xpath("/html/body/div[1]/div[2]/form/fieldset/div[2]/input").send_keys(pin)
        time.sleep(3)
        driver.find_element_by_xpath("/html/body/div[1]/div[2]/form/fieldset/div[3]/div[2]/input[4]").click()
        time.sleep(3)
        driver.get("https://purdue.brightspace.com/d2l/home/6824")
        driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/p[2]/a[1]").click()
        time.sleep(3)
        driver.get("https://purdue.brightspace.com/d2l/le/content/343395/Home")
        driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/div/div/div[6]/button[2]").click()

import requests
import d2lvalence.auth as d2lauth

# Keep getting invalid token problem - we might need to ask professor (or anyone with admin rights) to give us a key
appcreds = {'app_id': 'G9nUpvbZQyiPrk3um2YAkQ', 'app_key': 'ybZu7fm_JKJTFwKEHfoZ7Q'}
ac = d2lauth.fashion_app_context(app_id=appcreds['app_id'], app_key=appcreds['app_key'])
auth_rl = ac.create_url_for_authentication('devcop.brightspace.com', 'http://localhost:8080')
print(auth_rl)
redirect = 'http://localhost:8080?x_a=dC31ncmeHGvtullmp-6xSu&x_b=GPo8Rm7ou1fxZ7D8JHKOu1&x_c=093VuH_tHn1WGlla7pQ7MvGDJUX8lZ5gS5jwOgR8xNE'

# errors around here not because of format of method but because off app id and key
uc = ac.create_user_context(result_uri=redirect, host='devcop.brightspace.com', encrypt_requests=True)
print(uc)
route = '/d2l/api/versions/'
r = requests.get(uc.scheme + '://' + uc.host + route, auth=uc)
print(r.status_code)