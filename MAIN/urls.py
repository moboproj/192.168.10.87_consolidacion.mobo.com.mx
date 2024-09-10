
from django.urls import path
from . import views

from django.conf import settings
from django.contrib.staticfiles.urls import static
app_name = 'MAIN'
urlpatterns = [

    path('manu_MAIN/', views.menu_MAIN, name='menu_MAIN'),
    path('etl/',views.etl, name='etl'),# no se ocupa aun
    path('dashboard/',views.dashboard, name='dashboard'), #se queda
    path('Edashboard/', views.Edashboard, name='Edashboard'),
    path('SumaExBan/', views.SumaExBan, name='suma_extbanco'),
    path('totalesxtienda/', views.totalesxtienda, name='suma_hana'),
    path('vwTxT/', views.vwTxT, name='totalesXtienda'),
    path('nomach/', views.nomach, name='nomach'),
    
    # path('JoinCondolidacion/', views.JoinConsolidacion, name='JoinCondolidacion'),
    path('JoinAmex/', views.JoinAmex, name='JoinAmex'),
    path('tablero/', views.tablero, name='tablero'),
    #path para tablas de abrahamTabla_qa/
    path('vistaTotalxTienda/', views.vistaTotalxTienda, name='TXT'),
    # path('json_ventas_y_detalle/', views.ventas_detalles_v2, name='VD'),
    path('Detalles/', views.Tabla_detalle, name='Detalles'),
    path('TablaDiccionario/', views.TableDiccionario, name='diccionario'),
    # agregado con ivan
    path('EfectivoDashbord/',views.CONSOLIDACIONEFECTIVO, name='EfectivoDashbord'), #agregado por Ivan
    path('NewDashbord/',views.CONSOLIDACIONTIPO, name='NewDashbord'), # agregado por Ivan
    path('Diccionario_transacciones/', views.Diccionario_transacciones, name='diccionario2'),# agregado para consolidacion manual
    path('json_ventas_y_detalle/', views.ventas_detalles_v2, name='VD'),# agregado para consolidacion 
    path('modal_detalle/', views.modal_detalle,name='modal_detalle'), # agregado
    path('actualizar_registros/', views.actualizar_registros, name='actualizar_registros'), #actualizar
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)