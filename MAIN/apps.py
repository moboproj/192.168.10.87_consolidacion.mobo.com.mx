from django.apps import AppConfig
from django.core.cache import cache

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MAIN'
    
    def ready(self):
        cache.clear()
        from . import schedulerMain  # Deja esta línea solo si es necesario importar 'scheduler' aquí
        schedulerMain.getScheduler().start()
       

        