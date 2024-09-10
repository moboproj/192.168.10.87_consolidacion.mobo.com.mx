# from apscheduler.schedulers.background import BackgroundScheduler
# from django_apscheduler.jobstores import DjangoJobStore, register_events
# from django.utils import timezone
# from django_apscheduler.models import DjangoJobExecution
# import sys
# from .views import inicio

# # Esta es la función que deseas programar. Agrega todas las funciones que desees programar aquí.
# def deactivate_expired_accounts():
#     today = timezone.now()
#     print ("Deactivating expired accounts")
#     # Realiza las acciones necesarias, como desactivar cuentas vencidas.

# def start():
#     scheduler = BackgroundScheduler()
#     scheduler.add_jobstore(DjangoJobStore(), "default")
#     # Ejecutar esta tarea cada 24 horas.
#     # scheduler.add_job(inicio, 'interval', seconds=60, name='clean_accounts', jobstore='default')
#   scheduler.add_job(inicio, 'cron', hour=3, minute=0, second=0, name='daily_task', jobstore='default')

#     register_events(scheduler)
#     scheduler.start()
#     print("Scheduler started...", file=sys.stdout)