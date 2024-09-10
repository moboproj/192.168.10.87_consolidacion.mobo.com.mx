from django.urls import path
from . import views
# from .views import update_option, select_columns2

from django.conf import settings
from django.contrib.staticfiles.urls import static
app_name = 'extracpanda'

urlpatterns = [

    path('menu/',views.menu, name='menu'),
    path('extracto/',views.vistaExtracto, name='extracto'),
    path('update_option/',views.update_option, name='update_option'),
    path('select_columns2/',views.select_columns2, name='select_columns2'), ######
    path('enviar_route/', views.enviar_route, name='enviar_route'),
    path('amex/', views.amex, name='amex'),
    path('select_columnsAmex/', views.select_columnsAmex, name='select_columnsAmex'),
    path('tablas/', views.tablas, name='tablas'),
    path('select_columns2_Ivan/', views.TablaIvan, name='select_columns2_Ivan'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)