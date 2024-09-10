from django.apps import AppConfig


class HanaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'HANA'
    
    # def ready(self):
    #     from . import scheduler  # Deja esta línea solo si es necesario importar 'scheduler' aquí
    #     scheduler.start()
