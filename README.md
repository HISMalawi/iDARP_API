# MEDU_CDR_IDS_Data_Dictionary_API

This repository contains a Python Django API project. 
This guide will walk you through the steps to set up the Django environment required to run the API locally.

# Prerequisites
Before setting up the Django environment, make sure you have the following installed on your system:
1. Python 3.x: Install Python by following the instructions provided on the official Python website: https://www.python.org/downloads/
2. Pip: Python's package manager. It should be installed by default with Python 3.x.

# Setup Instructions
1. Clone the repository to your local machine.
2. Use the development-1.0 git branch when developing features and tests.
3. Create a virtual environment (recommended):
   - It is recommended to use a virtual environment to isolate the project dependencies. You can create a virtual environment using the following command: `python3 -m venv env`
   - Activate the virtual environment:
     - For Windows: `.\env\Scripts\activate`
     - For Unix or Linux: `source env/bin/activate`
4. Install project dependencies: `pip install -r requirements.txt`
   - This will install all the required packages and libraries specified in the requirements.txt file.
   - To make the packages persistent run the code `pip freeze > requirements.txt`
5. When you encounter an error during pip install from the psycopg2 package use the following codes
   - For CentOS/RHEL/Fedora Linux: `sudo yum install postgresql-devel python3-devel`
   - For PIP Install `psycopg2-binary`
   - For Debian/Ubuntu Linux: `sudo apt-get install libpq-dev python3-dev`
6. Database Configuration:
   - By default, the project is configured to use a SQLite database. 
   - If you want to use a different database, update the database settings in the settings.py file according to your requirements.
   - For development, we are using the GCP Database called: dev_test.
7. How to run migrations:
   - Edit `djtrigger` to `djtriggers` before running a migration, then revert after.
   - Replace `.venv/lib/djtriggers/migrations/` with `djtrigger/migrations/`
   - Edit all occurrences of `djtrigger` in the migrations to `djtriggers` in `.venv/lib/djtriggers/migrations/`
   - When you add new fields or models to an app in the API e.g. for an app called users run `python3 manage.py makemigrations users` to make new migrations
   - To persists the changes run the following `python3 manage.py migrate users`
   - We advise making migrations for a single app because of a bug in the API.
8. Create a superuser (admin account):
   - Run the following command and follow the prompts to create a superuser account: `python3 manage.py createsuperuser`
9. Run the development server: `python3 manage.py runserver`
   - The API should now be accessible at http://localhost:8000/. You can test the available endpoints using tools like cURL, Postman, or your web browser.

