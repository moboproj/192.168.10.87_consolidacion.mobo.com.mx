from django.urls import path
from . import views

from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    path('extract/',views.extract, name='extract'),    
    path('extractFolioSig/',views.extractFolioSig, name='extractFolioSig'),    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)