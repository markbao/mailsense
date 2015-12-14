#!/usr/bin/python

import httplib2

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from apiclient import errors

import re
import pprint
import dbinterface as db

import requests

# Set up pretty printer
pp = pprint.PrettyPrinter()

# Get whitelist array from RethinkDB
whitelist = db.get_whitelist('email')
print '\n+++ Printing email whitelist'
print whitelist

# Get threads array from DB
thread_whitelist = db.get_whitelist('thread')
print '\n+++ Printing thread approvals'
print thread_whitelist

# Set my email address
# TODO: auto-discover
ME_EMAIL = 'mark@markbao.com'

# Set label IDs
# TODO: auto-discover and maybe save
LABEL_INBOX = 'INBOX'
LABEL_PROCESSING = 'Label_137'
LABEL_NONESSENTIAL = 'Label_138'

# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = 'client_secret.json'

# Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.modify'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

# Start the OAuth flow to retrieve credentials
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
http = httplib2.Http()

# Try to retrieve credentials from storage or run the flow to generate them
credentials = STORAGE.get()
if credentials is None or credentials.invalid:
  credentials = run(flow, STORAGE, http=http)

# Authorize the httplib2.Http object with our credentials
http = credentials.authorize(http)

# Build the Gmail service from discovery
gmail_service = build('gmail', 'v1', http=http)

# Gmail functions from Google sample library, modified to use gmail_service
# TODO: Refactor Gmail functions to another place

def ListThreadsMatchingQuery(query=''):
  """List all Threads of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
           Eg.- 'label:UNREAD' for unread messages only.

  Returns:
    List of threads that match the criteria of the query. Note that the returned
    list contains Thread IDs, you must use get with the appropriate
    ID to get the details for a Thread.
  """
  try:
    response = gmail_service.users().threads().list(userId='me', q=query).execute()
    threads = []
    if 'threads' in response:
      threads.extend(response['threads'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = gmail_service.users().threads().list(userId='me', q=query,
                                        pageToken=page_token).execute()
      threads.extend(response['threads'])

    return threads
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def ListThreadsWithLabels(label_ids=[]):
  """List all Threads of the user's mailbox with label_ids applied.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Threads with these labelIds applied.

  Returns:
    List of threads that match the criteria of the query. Note that the returned
    list contains Thread IDs, you must use get with the appropriate
    ID to get the details for a Thread.
  """
  try:
    response = gmail_service.users().threads().list(userId='me',
                                              labelIds=label_ids).execute()
    threads = []
    if 'threads' in response:
      threads.extend(response['threads'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = gmail_service.users().threads().list(userId='me',
                                                labelIds=label_ids,
                                                pageToken=page_token).execute()
      threads.extend(response['threads'])

    return threads
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def GetThread(thread_id):
  """Get a Thread.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    thread_id: The ID of the Thread required.

  Returns:
    Thread with matching ID.
  """
  try:
    thread = gmail_service.users().threads().get(userId='me', id=thread_id, format='metadata').execute()
    messages = thread['messages']
    #print ('thread id: %s - number of messages '
    #       'in this thread: %d') % (thread['id'], len(messages))
    return thread
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def ModifyThread(thread_id, msg_labels):
  """Add labels to a Thread.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    thread_id: The id of the thread to be modified.
    msg_labels: The change in labels.

  Returns:
    Thread with modified Labels.
  """
  try:
    thread = gmail_service.users().threads().modify(userId='me', id=thread_id,
                                              body=msg_labels).execute()

    thread_id = thread['id']
    label_ids = thread['messages'][0]['labelIds']

    print 'Thread ID: %s - Processed directives: %s' % (thread_id, msg_labels)
    return thread
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def ModifyMessage(msg_id, msg_labels):
  """Modify the Labels on the given Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The id of the message required.
    msg_labels: The change in labels.

  Returns:
    Modified message, containing updated labelIds, id and threadId.
  """
  try:
    message = gmail_service.users().messages().modify(userId='me', id=msg_id,
                                                body=msg_labels).execute()

    label_ids = message['labelIds']

    print 'Message ID: %s - Processed directives: %s' % (msg_id, msg_labels)
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

def ProcessMessageSignals(email_subject, email_thread_from, email_thread_id, email_message_from):
  if email_thread_from is None:
    return 'nonessential'
  
  # TODO: Think about processing all other available emails

  judgment = 'nonessential'
  print 'email_thread_from: ' + email_thread_from.encode('utf-8')
  print 'email_message_from: ' + email_message_from.encode('utf-8')

  # Find sender email in from field
  thread_from_re = re.search(r'[\w\.-]+@[\w\.-]+', email_thread_from)
  message_from_re = re.search(r'[\w\.-]+@[\w\.-]+', email_message_from)
  
  thread_from = ""
  message_from = ""
  processing_failed = False
  
  if thread_from_re == None or message_from_re == None:
    # Regex failed; leave mail in Processing
    processing_failed = True
    judgment = 'error'
  else:
    thread_from = thread_from_re.group(0)
    message_from = message_from_re.group(0)
    print 'Processing %s with thread ID %s...' % (thread_from, email_thread_id)

    # Sent signal - Check if the latest message's sender is me
    if message_from == ME_EMAIL:
      # Sent message - overrides all
      print 'Sent from me'
      judgment = 'sent'
    else:
      # Sender signal - Check sender against whitelist
      if thread_from in whitelist:
        # All good, approved
        print 'Found in whitelist'
        judgment = 'essential'

      # Domain signal - Check sender's domain against whitelist
      if re.search("@[\w.]+", thread_from).group() in whitelist:
        print 'Found domain in whitelist'
        judgment = 'essential'

      # Thread signal - Check thread against thread database
      if email_thread_id in thread_whitelist:
        print 'Found thread %s in thread_whitelist' % email_thread_id
        return 'essential'

      # TODO - add word signal (e.g. urgent, important, etc.)

  return judgment

print '\n+++ Working on moved threads'

# First, process moved messages
# Get all threads in the Inbox and Nonessential category
moved_threads = ListThreadsWithLabels([LABEL_INBOX, LABEL_NONESSENTIAL])

for thread in moved_threads:
  # Get the thread info
  thread_id = thread['id']
  th = GetThread(thread_id)

  print 'Processing thread %s' % thread_id

  if thread_id not in thread_whitelist:
    # Authorization for thread in database
    thread_whitelist.add(thread_id)
    db.whitelist_thread(thread_id)
    print 'Pushed %s to approved threads list' % thread_id

    # Remove Nonessential label
    ModifyThread(thread_id, {'removeLabelIds': [LABEL_NONESSENTIAL]})

print '\n+++ Working on threads in Processing'

# Get all threads in the Processing category
processing_threads = ListThreadsWithLabels([LABEL_PROCESSING])

for thread in processing_threads:
  # Get the thread info
  thread_id = thread['id']

  print '\n<<<<<<<<<< Opening thread: %s <<<<<<<<<<' % thread_id

  th = GetThread(thread_id)
  # pp.pprint(th['messages'][0]['payload']['headers'])

  lastMessageIndex = len(th['messages']) - 1

  judgment = 'nonessential' # Default judgment

  # Get sender, subject, and from of first message
  subject = next((item['value'] for item in th['messages'][0]['payload']['headers'] if item['name'] == 'Subject'), None)
  thread_from = next((item['value'] for item in th['messages'][0]['payload']['headers'] if item['name'] == 'From'), next((item['value'] for item in th['messages'][0]['payload']['headers'] if item['name'] == 'from'), None))
  last_message_from = next((item['value'] for item in th['messages'][-1]['payload']['headers'] if item['name'] == 'From'), next((item['value'] for item in th['messages'][-1]['payload']['headers'] if item['name'] == 'from'), None))

  judgment = ProcessMessageSignals(subject, thread_from, thread_id, last_message_from)

  if judgment == 'essential':
    print 'JUDGMENT: essential'

    # Remove Processing label from thread
    ModifyThread(thread['id'], {'removeLabelIds': [LABEL_PROCESSING, LABEL_NONESSENTIAL]})

    # Move message to inbox using last message
    # This is so the notification shows *that message*
    # Not "5 new messages in [thread]"
    ModifyMessage(th['messages'][lastMessageIndex]['id'], {'addLabelIds': ['INBOX']})
  elif judgment == 'sent':
    print 'JUDGMENT: sent - removing processing label'
    print '          no other judgments, all other intact'

    # Remove Processing message and let it be in Sent
    ModifyThread(thread['id'], {'removeLabelIds': [LABEL_PROCESSING]})
  elif judgment == 'nonessential' or judgment == 'error':
    print 'JUDGMENT: ' + judgment

    # Remove Processing label, archive, and move to Nonessential
    ModifyThread(thread['id'], {'removeLabelIds': [LABEL_PROCESSING, LABEL_INBOX], 'addLabelIds': [LABEL_NONESSENTIAL]})

  print '>>>>>>>>>> Closing thread: %s >>>>>>>>>>' % thread_id
