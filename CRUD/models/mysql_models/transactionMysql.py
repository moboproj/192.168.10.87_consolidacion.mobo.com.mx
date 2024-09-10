from CRUD.models.mysql_models.transactionMysql import transactionMysql
from django.utils import timezone

class FolioSiguientePorSucursal(transactionMysql.Model):
    sucursal = transactionMysql.CharField(max_length=255)
    tipo = transactionMysql.CharField(max_length=255)
    folio = transactionMysql.CharField(max_length=255)