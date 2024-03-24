from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('<int:current_year>/<int:current_month>', views.all_calendars, name='all_calendars'),
]
