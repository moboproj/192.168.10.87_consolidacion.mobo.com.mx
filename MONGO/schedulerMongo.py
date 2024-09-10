# from apscheduler.schedulers.background import BackgroundScheduler
# from django_apscheduler.jobstores import DjangoJobStore, register_events
# from django.utils import timezone
# from django_apscheduler.models import DjangoJobExecution
# import sys
# from .views import iniciomongo

# # Esta es la función que deseas programar. Agrega todas las funciones que desees programar aquí.
# def deactivate_expired_accounts():
#     today = timezone.now()
#     print ("Deactivating expired accounts")
#     # Realiza las acciones necesarias, como desactivar cuentas vencidas.
#     ...

# def start():
#     schedulerMongo = BackgroundScheduler()
#     # scheduler.add_jobstore(DjangoJobStore(), "default")
#     # Ejecutar esta tarea cada 24 horas.
#     schedulerMongo.add_job(iniciomongo, 'interval', seconds=15, name='clean_accounts', jobstore='default')

#     register_events(schedulerMongo)
#     return schedulerMongo
    