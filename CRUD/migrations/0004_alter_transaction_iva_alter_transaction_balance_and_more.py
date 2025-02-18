# Generated by Django 4.1.11 on 2023-09-12 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CRUD', '0003_remove_transaction_formas_pago_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='IVA',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='balance',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='fp_amount',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='gross_up',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='importe_c_desc',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='priceWoVAT',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='subtotal',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='total',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='total_disc',
            field=models.FloatField(default=0.0),
        ),
    ]
