from flask import Flask, request
import redis
import os

env = os.getenv('ENV', 'dev')
print 'Running in env %s' % env

import dbinterface as db

app = Flask(__name__)

@app.route('/')
def index():
  return "Mailsense Server"

@app.route('/add', methods=['GET', 'POST'])
def add():
  if request.method == 'POST':
    email = request.form['email']

  if request.method == 'GET':
    email = request.args.get('email', '')

  # find email
  if db.whitelist_email(email):
    return 'ADD: pushed %s to whitelist' % email
  else:
    return 'ADD: %s already in whitelist' % email

@app.route('/delete', methods=['GET', 'POST'])
def delete():
  if request.method == 'POST':
    email = request.form['email']

  if request.method == 'GET':
    email = request.args.get('email', '')

  # find email
  if db.whitelist_email_delete(email):
    return 'DELETE: removed %s from whitelist' % email
  else:
    return 'DELETE: %s not in whitelist' % email

if __name__ == '__main__':
  if env == 'dev':
    app.run(debug=True)
  else:
    app.run('0.0.0.0', 8473)
