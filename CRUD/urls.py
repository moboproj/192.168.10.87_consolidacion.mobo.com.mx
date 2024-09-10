from django.urls import path
from . import views

from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    path('inicio/',views.inicio, name='inicio'),
    path('consultahana/',views.apihana, name='consultahana'),
    path('consultamobonet/',views.consultamobonet, name='consultamobonet'),
    path('consultamongo/',views.saveDataMongo, name='consultamongo'),
    path('extract/',views.extract, name='extract'),
    path('createInsert/',views.createInsert, name='createInsert'),
    path('extractFolioSig/',views.extractFolioSig, name='extractFolioSig'),
    path('preinsert/',views.etl, name='preinsert'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)