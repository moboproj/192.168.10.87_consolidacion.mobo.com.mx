from CRUD.models.hana_models.transactionHana import transactionHana
from django.utils import timezone


class extraxtTicket(transactionHana.Model):
    NumAtCard = transactionHana.CharField(max_length=255)
    DocNum = transactionHana.CharField(max_length=255)