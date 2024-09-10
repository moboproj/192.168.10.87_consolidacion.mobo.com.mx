from django.db import models
from django.utils import timezone



class extraxtTicket(models.Model):
    NumAtCard = models.CharField(max_length=255)
    DocNum = models.CharField(max_length=255)
    
    
class FolioSiguientePorSucursal(models.Model):
    sucursal = models.CharField(max_length=255)
    tipo = models.CharField(max_length=255)
    folio = models.CharField(max_length=255)