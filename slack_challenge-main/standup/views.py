import calendar
from django.shortcuts import render
from datetime import datetime, timedelta
from .models import CalendarModel
from .main import run

def get_each_day_of_month(current_year=datetime.now().year, current_month=datetime.now().month):
    """Return a list with each day of the month until today."""
    if current_year == datetime.now().year and current_month == datetime.now().month:
        # Deals with dates if not current month
        today = datetime.today()
    else:
        today = datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1])
    first_of_month = datetime(current_year, current_month, 1)
    delta = today - first_of_month
    return [(first_of_month + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days+1)]


def rearrange_object():
    """Rearranges calendar object to {name: {date: [text, emoji]}}."""
    calendars = CalendarModel.objects.order_by('-date')
    ordered_dict = {}
    for i in calendars:
        if i.user_name not in ordered_dict:
            ordered_dict[i.user_name] = {i.date: [i.text, i.emoji]}  # type(i.date) -> datetime.date
        else:
            ordered_dict[i.user_name].update({i.date: [i.text, i.emoji]})
    return ordered_dict


def refresh(request):
    """Pull newest/missing data from slack."""
    run()
    return all_calendars(request)


def all_calendars(request, current_year=datetime.now().year, current_month=datetime.now().month):
    """Add missing dates and check if a user is sick or on vacation."""
    today = datetime.today()
    month_days = get_each_day_of_month(current_year, current_month)
    ordered_dict = rearrange_object()
    new_dict = {}
    bad_boys = []
    for user in ordered_dict:  # adds missing days to dict where user didnt put any info
        new_dict[user] = {}
        for day in month_days:  # type(day) -> str, 2022-09-01
            day = datetime.strptime(day, "%Y-%m-%d").date()  # datetime.date
            if day not in ordered_dict[user]:
                new_dict[user].update({day: {"text": "none", "emoji": "none"}})
            else:
                new_dict[user].update({day: {"text": ordered_dict[user][day][0], "emoji": ordered_dict[user][day][1]}})
        new_dict[user] = dict(sorted(new_dict[user].items(), reverse=True))
    if current_month == datetime.now().month:
        for user in new_dict:
            if new_dict[user][today.date()]["text"] == "none" and today.strftime('%A') != 'Sunday' and today.strftime('%A') != 'Saturday':
                if ("palm" or "thermometer") not in new_dict[user][today.date()]["emoji"]:
                    bad_boys.append(user)

    return render(request,
                  "calendar/all_calendars.html",
                  {"calendars": new_dict,
                   "dates": month_days,
                   "current_year": current_year,
                   "current_month": int(current_month),
                   "current_real_year": datetime.now().month,
                   "beginning_month": 8,
                   "bad_boys": bad_boys
                   })
