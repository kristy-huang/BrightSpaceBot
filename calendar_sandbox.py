from pprint import pprint
from Google import Create_Service
from datetime import timedelta, datetime


CLIENT_SECRET_FILE = "client_secret.json"
API_NAME = "calendar"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)


def main():
    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('Getting List o 10 events')
    # getting the next 10 events from now ordered by startTime
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


def create_event(s, eventTitle, eventDescrp, startTime, endTime):
    eventBody = {"summary": eventTitle,
                 "description": eventDescrp,
                 "start": {"dateTime": startTime, "timeZone": 'Europe/London'},
                 "end": {"dateTime": endTime, "timeZone": 'Europe/London'},
                 "colorId": "1"}
    event_result = s.events().insert(calendarId='primary', body=eventBody).execute()

    print("created event")
    print("id: ", event_result['id'])
    print("summary: ", event_result['summary'])
    print("starts at: ", event_result['start']['dateTime'])
    print("ends at: ", event_result['end']['dateTime'])


def colors():
    colors = service.colors().get().execute()
    print(colors['calendar'])
    print("---")
    print(colors['event'])


if __name__ == '__main__':
    c = "2021-11-06T03:58:00.000Z"
    d = datetime.now().date()
    tomorrow = datetime.fromisoformat(c[:-1])
    start = tomorrow.isoformat()
    end = (tomorrow + timedelta(hours=1)).isoformat()

    create_event(service, "DUE ", "You have an assignment due bro", start, end)
    colors()
    #service.events().delete(calendarId='primary', eventId='0vlnbnun5mru0n8gjr38rkrvm4').execute() # to delete an event

    #event = service.events().get(calendarId='primary', eventId='eventId').execute()
    # events = service.events().list(calendarId='primary', q='DUE: adkfjadl').execute()
    # for event in events['items']:
    #     print(event["id"])
    #     print(event["summary"])
    #     print("ends at: ", event['end']['dateTime'])


