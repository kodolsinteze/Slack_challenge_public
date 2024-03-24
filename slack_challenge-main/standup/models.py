from django.db import models


class CalendarModel(models.Model):
    date = models.DateField()
    user_name = models.CharField(max_length=100, null=True)
    user_id = models.CharField(max_length=100, null=True)
    emoji = models.CharField(max_length=100, null=True)
    text = models.TextField(null=True)
