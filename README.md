
## Junior Dev challenge.

Required 3rd party libraries: 
* psycopg2

## How to run.

Open folder containing project and run `python manage.py runserver`

## How the program runs.

* The program pulls the user list from AISP-integrations and saves the user data in a `CalendarModel`. 
* The program then pulls the message data from the last pull and organises the data. If its an initial pull, the messages are pulled from 01.08.2022. 
* To run the program as a daily task automatically, add the main.py to a cronjob and it will update the mesage and user data.
* If a user is absent without a valid reason, the specific day will be marked in red. 
* If a user is sick, the specific day will be marked in blue. 
* If a user is on a vacation, the specific day will be marked in green.
* The info about the user is based on the emoji provided in slack.
