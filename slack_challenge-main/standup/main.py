"""Adds user data to database to be used by Django."""
from datetime import datetime, timedelta
import requests
import time
import json
import re
import psycopg2

START_DATE = datetime(2022, 8, 1)
START_DATE_TS = time.mktime(START_DATE.timetuple())
AUTH = 'Bearer'


def get_user_list():
    """Write users from AISP-integrations to a json file."""
    try:
        with open('standup/data.json') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    url = "https://slack.com/api/usergroups.users.list?usergroup=S01KJUSTK51"
    headers = {
        'Authorization': AUTH,
    }
    response = requests.request("GET", url, headers=headers)
    parsed = json.loads(response.text)
    for user in parsed["users"]:
        if user not in data:
            url = f"""https://slack.com/api/users.info?include_locale=true&user={user}"""
            headers = {
                'Authorization': AUTH
            }
            response = requests.request("GET", url, headers=headers)
            parsed_users = json.loads(response.text)
            data[user] = parsed_users["user"]["real_name"]

    with open('standup/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def subs(string):
    """Remove AISP hyperlink from text."""
    regex = r"<\S*\|(\S*)>"
    result = re.search(regex, string)
    while(result):
        sub = re.sub(regex, result.group(1), string, 1)
        result = re.search(regex, sub)
        string = sub
    try:
        return sub
    except UnboundLocalError:
        return string


def specific_sql_query(sql):
    """Send a user defined sql querry."""
    """establishing the connection"""
    conn = psycopg2.connect(
        database="slack_challenge",
        user='postgres',
        password='localpass',
        host='127.0.0.1',
        port='5433'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    sql = f'''{sql}'''

    """executing sql querry"""
    cursor.execute(sql)
    try:
        info = cursor.fetchall()
    except psycopg2.ProgrammingError:
        info = []
    conn.close()
    return info


def ts_to_date(ts):
    """Return a timestamp from datetime."""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')


def check_latest_date():
    """Return a timestamp for the latest date from the database."""
    sql = '''SELECT date FROM standup_calendarmodel ORDER BY date desc
    limit 1'''
    latest_date = specific_sql_query(sql)
    if len(latest_date) == 0:
        latest_date = time.mktime(datetime(2022, 8, 1).timetuple())
    else:
        latest_date = time.mktime(latest_date[0][0].timetuple())  # to ts
    return latest_date


def new_first_run(cursor=""):
    """Add the necessary data to the database in case the database is empty."""
    with open('standup/data.json') as f:
        user_data = json.load(f)
    sql = '''SELECT date FROM standup_calendarmodel ORDER BY date desc
    limit 1'''
    latest_date = specific_sql_query(sql)
    if len(latest_date) == 0:
        latest_date = time.mktime(datetime(2022, 8, 1).timetuple())
        url = f"""https://slack.com/api/conversations.history?channel=C01GDCUE79V&oldest={latest_date}&cursor={cursor}&limit=150&"""
        headers = {
            'Authorization': AUTH
        }
        response = requests.request("GET", url, headers=headers)
        parsed = json.loads(response.text)
        while("response_metadata" in parsed):
            for message in parsed["messages"]:
                loop_messages(message, user_data)
            cursor = parsed["response_metadata"]["next_cursor"]
            url = f"""https://slack.com/api/conversations.history?channel=C01GDCUE79V&oldest={latest_date}&cursor={cursor}&limit=150&"""
            headers = {
                'Authorization': AUTH
            }
            response = requests.request("GET", url, headers=headers)
            parsed = json.loads(response.text)
        for message in parsed["messages"]:
            loop_messages(message, user_data)


def loop_messages(message, user_data):
    """Loop thru and parse the messages json from slack.

    If the user and date is in dict, then update with the text field,
    otherwise insert a new row.
    """
    if "\u2022" in message["text"] and message["user"] in user_data:
        # Checks for Bulletpoint in message
        message['text'] = subs(message["text"])
        date = ts_to_date(float(message["ts"]))
        text = message["text"].replace("'", "''")
        # text = text.replace("'", "''")
        sql = f"""SELECT EXISTS (
            SELECT 1 from standup_calendarmodel
            WHERE  date = '{date}'
            AND    user_id = '{message['user']}'
            );"""
        msg_exists = specific_sql_query(sql)[0][0]
        if not msg_exists:
            print(f"Date {date} for {message['user']} is not added, inserting")
            sql = f"""insert into standup_calendarmodel(date, text, user_id, user_name)
                    values('{date}', '{text}', '{message['user']}',
                    '{user_data[message['user']]}');"""
            specific_sql_query(sql)
        else:
            print(f"""Date {date} for {message['user']} is
                already added, skipping""")


def new_daily_run(cursor=""):
    """Update db.

    Check the oldest message date in db and fetches new data
    from slack from the oldest date and updates db.
    """
    latest_date = check_latest_date()
    with open('standup/data.json') as f:
        user_data = json.load(f)
    url = f"""https://slack.com/api/conversations.history?channel=C01GDCUE79V&oldest={latest_date}&cursor={cursor}&limit=150&"""
    headers = {
        'Authorization': AUTH
    }
    response = requests.request("GET", url, headers=headers)
    parsed = json.loads(response.text)
    if "response_metadata" not in parsed:
        for message in parsed["messages"]:
            loop_messages(message, user_data)
    else:
        while("response_metadata" in parsed):
            for message in parsed["messages"]:
                loop_messages(message, user_data)
            cursor = parsed["response_metadata"]["next_cursor"]
            url = f"""https://slack.com/api/conversations.history?channel=C01GDCUE79V&oldest={latest_date}&cursor={cursor}&limit=150&"""
            headers = {
                'Authorization': AUTH
            }
            response = requests.request("GET", url, headers=headers)
            parsed = json.loads(response.text)
        for message in parsed["messages"]:
            loop_messages(message, user_data)


def new_emojis():
    """Check status of user.

    Adds emoji to the db.
    """
    sql = """select distinct user_id from standup_calendarmodel"""
    user_id = specific_sql_query(sql)
    user_id = [i[0] for i in user_id]
    today = datetime.today()
    today_date = datetime(today.year, today.month, today.day)
    url_user = "https://slack.com/api/users.info?include_locale=true&user="
    for user in user_id:
        payload = {}
        headers = {
            'Authorization': AUTH
        }
        response = requests.request("GET",
                                    url_user + user,
                                    headers=headers,
                                    data=payload
                                    )
        parsed = json.loads(response.text)
        emoji = parsed["user"]["profile"]["status_emoji"]
        if emoji == "":
            emoji = "NULL"
        else:
            emoji = f"""'{emoji}'"""
        user_name = parsed["user"]["real_name"]
        sql = '''SELECT date FROM standup_calendarmodel
                order by date desc
                limit 1
                '''
        latest_date = specific_sql_query(sql)[0][0]
        latest_date = datetime.strptime(str(latest_date), '%Y-%m-%d')
        if latest_date != today_date:
            sql = f"""insert into standup_calendarmodel(date, user_id, user_name, emoji)
                values
                ('{today.strftime("%Y-%m-%d")}',
                '{user}',
                '{user_name}',
                {emoji})"""
            specific_sql_query(sql)
        else:
            sql = f"""update standup_calendarmodel set emoji = {emoji}
                where date = '{today.strftime("%Y-%m-%d")}'
                and user_id = '{user}'"""
            specific_sql_query(sql)


def get_each_day_of_month():
    """Return a list with each day of the month until today."""
    today = datetime.today()
    first_of_month = datetime(today.year, today.month, 1)
    delta = today - first_of_month
    return [(first_of_month +
            timedelta(days=i)).strftime('%Y-%m-%d') for i in
            range(delta.days+1)]

def run():
    """Run the required functions for data pull from slack"""
    get_user_list()
    new_first_run()
    new_daily_run()
    new_emojis()
