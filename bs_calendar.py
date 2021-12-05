from Google import Create_Service


class Calendar:
    def __init__(self):
        API_NAME = 'calendar'
        API_VERSION = 'v3'
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        CLIENT_FILE = 'client_secret.json'
        self.service = Create_Service(CLIENT_FILE, API_NAME, API_VERSION, SCOPES)

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
        print("created event")
        print("id: ", event['id'])
        print("summary: ", event['summary'])
        print("starts at: ", event['start']['dateTime'])
        print("ends at: ", event['end']['dateTime'])

    # adds a recurring event to the google calendar
    def insert_event_recurring(self, eventTitle, eventDescription, startTime, endTime, days):
        # TODO change colorID to be a color they want (maybe)
        # Note: timezone is "Europe/London" because it is in UTC time for BrightSpace. It will reflect properly
        # to the settings of the users calendar

        # create body of event with specifications
        eventBody = {"summary": eventTitle,
                     "description": eventDescription,
                     "start": {"dateTime": startTime, "timeZone": 'America/New_York'},
                     "end": {"dateTime": endTime, "timeZone": 'America/New_York'},
                     "recurrence": [
                         f"RRULE:FREQ=WEEKLY;BYDAY={days}"
                     ],
                     "colorId": "1"}

        # insert the event into the calendar
        event = self.service.events().insert(calendarId='primary', body=eventBody).execute()
        print("created event")
        print("id: ", event['id'])
        print("summary: ", event['summary'])
        print("starts at: ", event['start']['dateTime'])
        print("ends at: ", event['end']['dateTime'])
        print("recurring ", days)
        return event['id']

    # Based on the event title, find the event ID
    def get_event_from_name(self, eventTitle):
        events = self.service.events().list(calendarId='primary', q=eventTitle).execute()
        if len(events['items']) == 0:
            return -1, -1  # could not find event (there are multiples so we couldn't update properly)
        return events['items'][0]["id"], events['items'][0]['end']['dateTime']

    # get and return a list of instances of the recurring event
    def get_recurring_event(self, recurring_event_id):
        events = self.service.events().instances(calendarId='primary', eventId=recurring_event_id).execute()
        return events['items'][0]

    # To delete an event from the calendar
    def delete_event(self, eventID):
        self.service.events().delete(calendarId='primary', eventId=eventID).execute()
