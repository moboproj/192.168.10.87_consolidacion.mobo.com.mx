from django.core.wsgi import get_wsgi_application
import os 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consolidacionBancaria.settings')
application = get_wsgi_application()

from MAIN.views import JoinAmex

JoinAmex(None) #pase None como argumento para el parametro 'request' si no utiliza la funcion