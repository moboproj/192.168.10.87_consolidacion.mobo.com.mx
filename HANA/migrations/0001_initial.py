# Generated by Django 4.2.6 on 2023-10-19 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='extraxtTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NumAtCard', models.CharField(max_length=255)),
                ('DocNum', models.CharField(max_length=255)),
            ],
        ),
    ]
