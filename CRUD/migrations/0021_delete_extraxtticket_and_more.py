# Generated by Django 4.2.6 on 2023-10-19 22:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('CRUD', '0020_historictransaction_numline_transacctionpago_numline'),
    ]

    operations = [
        migrations.DeleteModel(
            name='extraxtTicket',
        ),
        migrations.DeleteModel(
            name='FolioSiguientePorSucursal',
        ),
        migrations.DeleteModel(
            name='historicTransaction',
        ),
        migrations.DeleteModel(
            name='transaccionHana',
        ),
        migrations.DeleteModel(
            name='TransacctionPago',
        ),
    ]
