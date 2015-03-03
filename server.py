from flask import Flask, request
import redis
import os

env = os.getenv('ENV', 'dev')
print 'Running in env %s' % env

# Connect to Redis
r = redis.StrictRedis(host='localhost', port=6379, db=0, password="REPLACE_ME")

app = Flask(__name__)

@app.route('/')
def index():
  return "emailsrv"

@app.route('/add', methods=['GET', 'POST'])
def add():
  if request.method == 'POST':
    email = request.form['email']

  if request.method == 'GET':
    email = request.args.get('email', '')

  # refresh whitelist 
  whitelist = r.lrange('whitelist', 0, -1)

  # find email
  if email not in whitelist:
    r.rpush('whitelist', email)
    return 'ADD: pushed %s to whitelist' % email
  else:
    return 'ADD: %s already in whitelist' % email

@app.route('/delete', methods=['GET', 'POST'])
def delete():
  if request.method == 'POST':
    email = request.form['email']

  if request.method == 'GET':
    email = request.args.get('email', '')

  # refresh whitelist 
  whitelist = r.lrange('whitelist', 0, -1)

  # find email
  if email in whitelist:
    r.lrem('whitelist', 0, email)
    return 'DELETE: removed %s from whitelist' % email
  else:
    return 'DELETE: %s not in whitelist' % email

if __name__ == '__main__':
  if env == 'dev':
    app.run(debug=True)
  else:
    app.run('0.0.0.0', 8473)
