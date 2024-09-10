from django.db import models
from django.utils import timezone

# Create your models here.
class libro(models.Model):
    id= models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='imagenes/',verbose_name="iamgen", null=True)
    descripcion = models.TextField(null=True,verbose_name="Descripcion")
    
    def __str__(self):
        fila = "Titulo: " + self.titulo + " - " + "Descripcion: " + self.descripcion
        return fila
    
    def delete(self, using=None, keep_parents=False):
        self.imagen.storage.delete(self.imagen.name)
        super().delete()
        
class fichasdeposito(models.Model):
    class Meta:
        managed = False
        db_table = 'fichasdeposito'
    IdFichaDeposito = models.AutoField(primary_key=True)
    FkIdTienda = models.IntegerField()  # Podría ser AutoField dependiendo del caso
    Deposito = models.DecimalField(max_digits=10, decimal_places=2)  # Usamos DecimalField para números decimales
    Fecha = models.DateField()
    Tipo = models.CharField(max_length=125)
    ArchivoMobo = models.CharField(max_length=250)
    Rechazado = models.BooleanField()
    Motivo = models.CharField(max_length=45)
    Comentario = models.CharField(max_length=250)
    Mail = models.CharField(max_length=250)
    


# class transaccionHana(models.Model):
#     codigo = models.CharField(max_length=255)
#     skuHana = models.CharField(max_length=255)
#     descr = models.CharField(max_length=255)
#     catego = models.CharField(max_length=255)
    
# class extraxtTicket(models.Model):
#     NumAtCard = models.CharField(max_length=255)
#     DocNum = models.CharField(max_length=255)
    
class SYS_PDEVOLUCIONES(models.Model):
    skComplet = models.CharField(max_length=255)
    venta_sk0 = models.CharField(max_length=255)
    guardado = models.CharField(max_length=255)
    
class SYS_PDETALLETRANS(models.Model):
    skComplet = models.CharField(max_length=255)
    venta_sk0 = models.CharField(max_length=255)
    guardado = models.CharField(max_length=255)
    
class SYS_PPAGOTANS(models.Model):
    skComplet = models.CharField(max_length=255)
    venta_sk0 = models.CharField(max_length=255)
    guardado = models.CharField(max_length=255)
    
class SYS_PTRANSACCIONES(models.Model):
    skComplet = models.CharField(max_length=255)
    venta_sk0 = models.CharField(max_length=255)
    guardado = models.CharField(max_length=255)
    
class SYS_PCOBROTRANS(models.Model):
    skComplet = models.CharField(max_length=255)
    venta_sk0 = models.CharField(max_length=255)
    guardado = models.CharField(max_length=255)
    
class SYS_PDETALLEDEVOL(models.Model):
    skComplet = models.CharField(max_length=255)
    venta_sk0 = models.CharField(max_length=255)
    guardado = models.CharField(max_length=255)
    
# class FolioSiguientePorSucursal(models.Model):
#     sucursal = models.CharField(max_length=255)
#     tipo = models.CharField(max_length=255)
#     folio = models.CharField(max_length=255)

# class historicTransaction(models.Model):
#     venta_sk = models.CharField(max_length=255)
#     venta_sk_n = models.CharField(max_length=255)
#     priceListId = models.CharField(max_length=255)
#     sucursal = models.CharField(max_length=10)
#     caja = models.CharField(max_length=10)
#     almacen = models.CharField(max_length=10)
#     hora24h = models.CharField(max_length=10)
#     ffecha = models.CharField(max_length=10)
#     horastr = models.CharField(max_length=10)
#     codeSucursal = models.CharField(max_length=10)
#     fecha_process = models.CharField(max_length=10)
#     sellerID = models.CharField(max_length=255)
#     SKU = models.CharField(max_length=255)
#     quantity = models.CharField(max_length=255)
#     priceWoVAT = models.CharField(max_length=255)
#     IVA = models.CharField(max_length=255)
#     total_disc = models.CharField(max_length=255)
#     precio_brutoSD = models.CharField(max_length=255)
#     subtotal = models.CharField(max_length=255)
#     partyIdentifier = models.CharField(max_length=255)
#     partyCode = models.CharField(max_length=255)
#     total = models.CharField(max_length=255)
#     fp_amount = models.CharField(max_length=255)
#     cambio = models.CharField(max_length=255)
#     fp_code = models.CharField(max_length=255)
#     fp_codeName = models.CharField(max_length=255)
#     fopa = models.CharField(max_length=255)
#     FolioSig = models.CharField(max_length=255)
#     pncd = models.CharField(max_length=255)
#     description = models.CharField(max_length=255)
#     barcode = models.CharField(max_length=255)
#     guardado = models.CharField(max_length=255)
#     NumLine = models.CharField(max_length=255)
#     created_at = models.DateTimeField(default=timezone.now)