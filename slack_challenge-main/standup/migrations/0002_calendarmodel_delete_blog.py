# Generated by Django 4.1 on 2022-09-01 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('standup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalendarModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('user_name', models.CharField(max_length=100, null=True)),
                ('user_id', models.CharField(max_length=100, null=True)),
                ('emoji', models.CharField(max_length=100, null=True)),
                ('text', models.TextField(null=True)),
            ],
        ),
        migrations.DeleteModel(
            name='blog',
        ),
    ]
