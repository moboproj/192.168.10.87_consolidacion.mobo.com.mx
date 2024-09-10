from django.apps import AppConfig

class MongoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MONGO'
    
#     def ready(self):
#         from . import schedulerMongo  # Deja esta línea solo si es necesario importar 'scheduler' aquí
#         schedulerMon = schedulerMongo.start()
#         schedulerMon.start()
