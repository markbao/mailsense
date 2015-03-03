#!/usr/bin/python

import rethinkdb as r
r.connect( "localhost", 28015).repl()
db = r.db('mailsense')

def get_whitelist(category):
  if (category == 'email' or category == 'thread'):
    whitelist = set()

    cursor = db.table(category + '_whitelist').run()
    for doc in cursor:
      if category == 'email':
        whitelist.add(doc['email'])
      elif category == 'thread':
        whitelist.add(doc['thread_id'])

    return whitelist

def whitelist_email(email):
  # Check for existence of email in DB
  num = db.table('email_whitelist').get_all(email, index='email').count().run()

  if num == 0:
    # Insert
    db.table('email_whitelist').insert({'email': email}).run()
    return True
  else:
    return False

def whitelist_thread(thread_id):
  # Check for existence of thread in DB
  num = db.table('thread_whitelist').get_all(thread_id, index='thread_id').count().run()

  if num == 0:
    # Insert
    db.table('thread_whitelist').insert({'thread_id': thread_id, 'created_at': r.now()}).run()
    return True
  else:
    return False