# -*- coding: utf-8 -*-

# 1. Go here:
#       https://console.developers.google.com/flows/enableapi?apiid=gmail
#    and create a new project for Oauth 2.0 of type "Other".
#    Download the client secret, name it client_secret.json,
#    and .gitignore it.
#
# 2. Run this:
#       $ pip install --upgrade google-api-python-client
#
# 3. Run the program:
#       $ python quickstart.py

from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import base64
import collections
import re

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Quickstart'

def get_file_path(dir_name, file_name):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    nested_dir = os.path.join(current_dir, dir_name)

    if not os.path.exists(nested_dir):
        os.makedirs(nested_dir)
    file_path = os.path.join(nested_dir, file_name)

    return file_path

def get_credentials(i):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    credential_path = get_file_path('.credentials' + str(i), 'gmail-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def get_body(msg):
    return base64.urlsafe_b64decode(str(msg["payload"]["parts"][0]["body"]["data"]))

def mark_as_read(service, msg):
    body = {"removeLabelIds": ['UNREAD','INBOX','IMPORTANT']}
    resp = service.users().messages().modify(userId='me', id=msg["id"], body=body).execute()
    return

def unsubscribe(service, msg):
    body = get_body(msg)
    # This is ugly.

    # Find unsubscribe link
    link_regex = re.search(r"unsubscribe.*?((?:[a-z][\w-]+:(?:\/{1,3}|[a-z0-9%])|www\d{0,3}[\.]|[a-z0-9\.\-]+[\.‌​][a-z]{2,4}\/)(?:[^\n\s\(\)<>]+|(([^\n\s\(\)<>]+|(([^\n\s\(\)<>]+)))*))+(?:(([^\n\s\(\)<>]+|(‌​([^\n\s\(\)<>]+)))*)|[^\n\s`!\(\)\[\]{};:'\".,<>?«»“”‘’]))", body)
    if(link_regex == None):
        return False

    # First capture group
    link = link_regex.group(1)

    # Click it
    response, content = httplib2.Http().request(link, 'GET')

    if(response['status'] == 200):
        print(content)
        return mark_as_read(service, msg)

    return False


def leave(service, msg):
    return True

def see_more(service, msg):
    print(msg["snippet"])
    key = raw_input()

    # d for done
    if(key == 'd'):
        return True

    print(get_body(msg))
    react(service, msg)

def save_for_later(service, msg):
    schedule_path = get_file_path('.tables', 'schedule_data.json')

    store = oauth2client.file.Storage(schedule_path)
    schedule_entries = store.get()

    if not schedule_entries or schedule_entries.invalid:
        schedule_entries = []

    schedule_for_msg = schedule_entries[msg["id"]]

    if schedule_for_msg and not schedule_for_msg.invalid:
        print("Schedule already exists:")
        print(schedule_for_msg)
        print("Reschedule?")
        if(raw_input() != 'y'):
            return

    schedule_for_msg = raw_input()

    return schedule_for_msg
    #store the message ID
    #store when you want to see it
    #display it again when some part of the program repeats
    #and the current time is greater than the stored time,
    #but not before.
    #probably save this externally in case the program stops running.
    #that way you can see it in like a month.
    #run something at the beginning to check.

def react(service, msg):
    actions = {
        'r': mark_as_read,
        's': save_for_later,
        'l': leave,
        'c': see_more,
        'u': unsubscribe
    }
    key = raw_input()
    result = actions[key](service, msg)
    print(result)

def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """

    for i in range(6):
        credentials = get_credentials(i)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
        results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()

        print(service.users().getProfile(userId='me').execute()["emailAddress"])

        if not results:
            print('No results found.')
        else:
            print('Results:')
            if "messages" in results:
                for mes in results["messages"]:
                    msg = service.users().messages().get(userId='me', id=mes["id"]).execute()
                    print("".join([i["value"] for i in msg["payload"]["headers"] if i["name"] == "Subject"]))
                    react(service, msg)


if __name__ == '__main__':
    main()