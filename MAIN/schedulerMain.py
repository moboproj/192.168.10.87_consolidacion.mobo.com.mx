from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.utils import timezone
from django_apscheduler.models import DjangoJobExecution
import sys
from .views import inicio
from django.core.cache import cache

cache.clear()

def getScheduler():
    schedulerMain = BackgroundScheduler()
    # Ejecutar esta tarea cada 24 horas.
    # scheduler.add_job(inicio, 'interval', minutes=60, name='clean_accounts', jobstore='default')
    # schedulerMain.add_job(inicio, 'interval', seconds=5 ,name='test', replace_existing=True)
   # schedulerMain.scheduled_job(inicio, 'interval', seconds=10 ,name='test' )
    register_events(schedulerMain)
    
    return schedulerMain
