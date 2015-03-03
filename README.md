![Mailsense](http://i.imgur.com/aedUnj4.png)

**Mailsense** is an **email management system** that aims to make your email experience suck less. We all get too much email. Mailsense aims to put your email in the right place, so you can see the important stuff, skim through the not-so-important stuff, and get fewer notifications during the course of your day.

For the design philosophy behind Mailsense, see [A proposal for a whitelist email management system](http://markbao.com/notes/organizing-email).

## How to use

### Requirements

Gmail or Google Apps account
Python 2.7+
pip 6.0+

### Set up Google API

1. Create a project in [Google Developer Console](https://console.developers.google.com/project).
2. In the project, go to **APIs & Auth > Credentials**.
3. Under OAuth, click **Create new Client ID**.
4. Create a new **Service Account**.
5. In the new Service Account section, click **Download JSON** to get your client secret file.
6. Rename this file to `client_secret.json` and move it to the root directory of this repo.

### Set up the system

Install requirements:

````
pip install -r requirements.txt
````

First run for the engine:

````
python engine.py
````

This will pop up Google OAuth in your browser, allowing you to authenticate.

TODO: Complete the rest of this

## TODO

- Auto-discover label IDs so we don't have to hard-code them
- Auto-discover current user email address so we don't have to hard-code it

©2015 Mark Bao. Withholding source license for now.