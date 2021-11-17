import requests
from Authentication import get_brightspace_session_auto
from database.db_utilities import DBUtilities

HEADER = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }
dbu = DBUtilities("./database/db_config.py")
'''
url = "https://purdue.brightspace.com/d2l/common/dialogs/quickLink/quickLink.d2l?ou=342361&type=lti&rCode=354644E0-4CD8-419D-A32F-4E78D8778E5C-3957388"
session = get_brightspace_session_auto(dbu, "kxtest1")
res = session.get(url, headers=HEADER)
print(res.status_code)'''


from bs_utilities import BSUtilities

bsu = BSUtilities(debug=True)
bsu.set_session_auto(dbu,"kxtest1")

print(bsu.check_kaltura(342361, 8012047))