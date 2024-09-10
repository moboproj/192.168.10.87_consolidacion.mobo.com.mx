"""
WSGI config for consolidacionBancaria project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os,sys
from django.core.wsgi import get_wsgi_application


sys.path.append('/var/www/html/uat.consolidacionbancaria.mobo.com.mx/public_html/consolidacionBancaria')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consolidacionBancaria.settings')

application = get_wsgi_application()

