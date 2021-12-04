from Google import Create_Service


class Calendar:
    def __init__(self):
        API_NAME = 'calendar'
        API_VERSION = 'v3'
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        CLIENT_FILE = 'client_secret.json'
        self.service = Create_Service(CLIENT_FILE, API_NAME, API_VERSION, SCOPES, 'x')

    # This method adds a singular event to the calendar
    def insert_event(self, eventTitle, eventDescription, startTime, endTime):
        # TODO change colorID to be a color they want (maybe)
        # Note: timezone is "Europe/London" because it is in UTC time for BrightSpace. It will reflect properly
        # to the settings of the users calendar

        # create body of event with specifications
        eventBody = {"summary": eventTitle,
                     "description": eventDescription,
                     "start": {"dateTime": startTime, "timeZone": 'Europe/London'},
                     "end": {"dateTime": endTime, "timeZone": 'Europe/London'},
                     "colorId": "1"}

        # insert the event into the calendar
        event = self.service.events().insert(calendarId='primary', body=eventBody).execute()

        '''print("created event")
        print("id: ", event['id'])
        print("summary: ", event['summary'])
        print("starts at: ", event['start']['dateTime'])
        print("ends at: ", event['end']['dateTime'])'''

    # Based on the event title, find the event ID
    def get_event_from_name(self, eventTitle):
        events = self.service.events().list(calendarId='primary', q=eventTitle).execute()
        print(events['items'])
        if len(events['items']) > 1 or len(events['items']) == 0:
            return -1, -1  # could not find event (there are multiples so we couldn't update properly)
        return events['items'][0]["id"], events['items'][0]['end']['dateTime']

    # To delete an event from the calendar
    def delete_event(self, eventID):
        self.service.events().delete(calendarId='primary', eventId=eventID).execute()

