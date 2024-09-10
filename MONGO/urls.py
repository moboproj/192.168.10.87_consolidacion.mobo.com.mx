from django.urls import path
from . import views

from django.conf import settings
from django.contrib.staticfiles.urls import static
app_name = 'MONGO'

urlpatterns = [
    path('craftMongo/',views.craftMongo, name='craftMongo'),
    path('newmongo/', views.newmongoV2, name='newmongo'),
    # path('QA_db/', views.test_connection, name='QA_db')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)