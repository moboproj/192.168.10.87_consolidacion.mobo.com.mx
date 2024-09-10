from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .models import extraxtTicket
from .models import FolioSiguientePorSucursal
from datetime import datetime, timedelta
from pymongo.errors import ServerSelectionTimeoutError
from django.db import connection
from MONGO.models import TransacctionPago

import requests
import json


# necesita fichasdeposito en el modelo 
# def consultamobonet(request):# se mueven de appa 
#     limit = 11  # Número de registros a mostrar
#     data_list = fichasdeposito.objects.using('mobonet').all()[:limit]  # Obtener los primeros 'limit' registros
#     return render(request, 'extract/mobonet.html', {'data_list': data_list})
    
def apihana(request):#se mueve de app 
    # return HttpResponse("apihana")
    url = 'http://api.hana.com.mx/VentaDiaria'
    api_key = '25f9e794323b453885f5181f1b624d0b'
    data = {
        "FilterEq": {
            "FechaInicio": "2023-08-30"
        }
    }
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response_data = response.json()
        data_list = response_data.get("Data", [])  # Usar get para evitar errores si "Data" no existe
        return render(request, "extract/index.html", {'data_list': data_list})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500) 
    

def api_hana(data):
    # return HttpResponse('api_hana')
    url = 'http://api.hana.com.mx/DinamicoQueryHana'
    api_key = '25f9e794323b453885f5181f1b624d0b'

    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json',
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Verificar si hubo errores en la solicitud HTTP

        # Decodificar la respuesta JSON si la hay
        response_data = response.json()
        return response_data
    except requests.exceptions.RequestException as e:
        return f'Error en la solicitud HTTP: {str(e)}'

    # Uso de la función
    data = {"key": "value"}  # Reemplaza esto con los datos que desees enviar
    response = api_hana_activar_sap(data)
    print(response)


def extract(request):
    # return HttpResponse('extract')
    fecha_actual = datetime.now()
    regreso = extractDataDocNum(fecha_actual)

    if regreso:
        return render(request, "extract/hana.html", {'result': "Se logró"})
    else:
        return HttpResponse("No se logró")

def extractDataDocNum(fecha_actual):
    # return HttpResponse('extractDataDocNum')
    fechaResta = fecha_actual - timedelta(days=250)
    fecha_actual_str = fecha_actual.strftime('%Y-%m-%d')
    fechaResta_str = fechaResta.strftime('%Y-%m-%d')    

    try:
        insert = {
            "FilterEq": {
                "Query": f'SELECT "NumAtCard", "DocNum" FROM "MOBO_PRODUCTIVO".ODLN WHERE \"NumAtCard\" LIKE \'0262%\' OR "NumAtCard" LIKE \'0304%\' OR "NumAtCard" LIKE \'0031%\' OR "NumAtCard" LIKE \'0016%\' OR "NumAtCard" LIKE \'0813%\' OR "NumAtCard" LIKE \'0262%F%\' OR "NumAtCard" LIKE \'0304%F%\' OR "NumAtCard" LIKE \'0031%F%\' OR "NumAtCard" LIKE \'0016%F%\' OR "NumAtCard" LIKE \'0813%F%\' OR "NumAtCard" LIKE \'0262%N%\' OR "NumAtCard" LIKE \'0304%N%\' OR "NumAtCard" LIKE \'0031%N%\' OR "NumAtCard" LIKE \'0016%N%\' OR "NumAtCard" LIKE \'0813%N%\' AND "DocType" = \'I\' AND "DocDate" BETWEEN \'{fecha_actual_str}\' AND \'{fechaResta_str}\'UNION ALL SELECT "NumAtCard", "DocNum" FROM "MOBO_PRODUCTIVO".OINV WHERE \"NumAtCard\" LIKE \'0262%\' OR "NumAtCard" LIKE \'0304%\' OR "NumAtCard" LIKE \'0031%\' OR "NumAtCard" LIKE \'0016%\' OR "NumAtCard" LIKE \'0813%\' OR "NumAtCard" LIKE \'0262%F%\' OR "NumAtCard" LIKE \'0304%F%\' OR "NumAtCard" LIKE \'0031%F%\' OR "NumAtCard" LIKE \'0016%F%\' OR "NumAtCard" LIKE \'0813%F%\' OR "NumAtCard" LIKE \'0262%N%\' OR "NumAtCard" LIKE \'0304%N%\' OR "NumAtCard" LIKE \'0031%N%\' OR "NumAtCard" LIKE \'0016%N%\' OR "NumAtCard" LIKE \'0813%N%\' AND "DocType" = \'I\' AND "DocDate" BETWEEN \'{fecha_actual_str}\' AND \'{fechaResta_str}\'UNION ALL SELECT "NumAtCard", "DocNum" FROM "MOBO_PRODUCTIVO".ORIN WHERE \"NumAtCard\" LIKE \'0262%\' OR "NumAtCard" LIKE \'0304%\' OR "NumAtCard" LIKE \'0031%\' OR "NumAtCard" LIKE \'0016%\' OR "NumAtCard" LIKE \'0813%\' OR "NumAtCard" LIKE \'0262%F%\' OR "NumAtCard" LIKE \'0304%F%\' OR "NumAtCard" LIKE \'0031%F%\' OR "NumAtCard" LIKE \'0016%F%\' OR "NumAtCard" LIKE \'0813%F%\' OR "NumAtCard" LIKE \'0262%N%\' OR "NumAtCard" LIKE \'0304%N%\' OR "NumAtCard" LIKE \'0031%N%\' OR "NumAtCard" LIKE \'0016%N%\' OR "NumAtCard" LIKE \'0813%N%\' AND "DocType" = \'I\' AND "DocDate" BETWEEN \'{fecha_actual_str}\' AND \'{fechaResta_str}\' UNION ALL SELECT "NumAtCard", "DocNum" FROM "MOBO_PRODUCTIVO".ORDN WHERE \"NumAtCard\" LIKE \'0262%\' OR "NumAtCard" LIKE \'0304%\' OR "NumAtCard" LIKE \'0031%\' OR "NumAtCard" LIKE \'0016%\' OR "NumAtCard" LIKE \'0813%\' OR "NumAtCard" LIKE \'0262%F%\' OR "NumAtCard" LIKE \'0304%F%\' OR "NumAtCard" LIKE \'0031%F%\' OR "NumAtCard" LIKE \'0016%F%\' OR "NumAtCard" LIKE \'0813%F%\' OR "NumAtCard" LIKE \'0262%N%\' OR "NumAtCard" LIKE \'0304%N%\' OR "NumAtCard" LIKE \'0031%N%\' OR "NumAtCard" LIKE \'0016%N%\' OR "NumAtCard" LIKE \'0813%N%\' AND "DocType" = \'I\' AND "DocDate" BETWEEN \'{fecha_actual_str}\' AND \'{fechaResta_str}\''
            }
        }
        responseExtract = api_hana(insert)
        # return JsonResponse(responseExtract)

        for item in responseExtract['Data']:
            DocNum = item['DocNum']
            NumAtCard = item['NumAtCard']
            extractTi = extraxtTicket(
                DocNum=DocNum,
                NumAtCard=NumAtCard,
            )
            extractTi.save(using='default')

        return True
    except ConnectionError as conn_error:
        return False
    except ServerSelectionTimeoutError as timeout_error:
        return False
    except Exception as e:
        return False
    

def selectSucu():
    # return HttpResponse("selectSucu")
    with connection.cursor() as cursor:
        cursor.execute("SELECT SUBSTRING(venta_sk, 8, 1) AS tipo_transaccion, sucursal, COUNT(*) AS repeticiones FROM consolidacion_bancarianueva.crud_transacctionpago GROUP BY SUBSTRING(venta_sk, 8, 1), sucursal")
        results = cursor.fetchall()

    return results 


def extractFolioSig(response):
    # return HttpResponse("extractFolioSig")
    results = selectSucu()
    # return HttpResponse(results)
    
    for resu in results:
        tipo = resu[0]
        sucursal = resu[1]
        response = get_folio_for_sucursal(tipo, sucursal)
        if response.get('Code') == 200 and response.get('Data'):
            folio = response['Data'][0].get('FOLIO')
            
            saveFolioSiguientePorSucursal = FolioSiguientePorSucursal(
                    # FolioSig=folio,
                    tipo=tipo,
                    sucursal=sucursal,
                    folio=folio,
            )
            saveFolioSiguientePorSucursal.save(using='default')
            
            transactions_to_update = TransacctionPago.objects.filter(sucursal=sucursal)
            transactions_to_update.update(FolioSig=folio)  # Actualiza todos los registros de una vez
            

    return HttpResponse("se logro")


def get_folio_for_sucursal(tipo, sucursal):
    # return  HttpResponse("get_folio_for_sucursal")
    if tipo == 'V':
        query = f'SELECT "U_SYS_FOLI" AS FOLIO FROM "MOBO_QA"."@SYS_PFOLIOVENTAS" WHERE "Name" = \'{sucursal}\''
    elif tipo == 'F':
        query = f'SELECT "U_SYS_FOLI" AS FOLIO FROM "MOBO_QA"."@SYS_PFOLIOFACTURAS" WHERE "Name" = \'{sucursal}\''
    elif tipo == 'D':
        query = f'SELECT "U_SYS_FOLI" AS FOLIO FROM "MOBO_QA"."@SYS_PFOLIODEVOL" WHERE "Name" = \'{sucursal}\''
    elif tipo == 'N':
        query = f'SELECT "U_SYS_FOLI" AS FOLIO FROM "MOBO_QA"."@SYS_PFOLIONOTACREDI" WHERE "Name" = \'{sucursal}\''
    else:
        query = None  
    
    if query:
        folio_query = {
            "FilterEq": {
                "Query": query
            }
        }
        response = api_hana(folio_query)
    else:
        response = None  

    return response    
          
# def docNum(param):
    
#     with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM V_vista_procesoV2 WHERE venta_sk = %s", [param])
#             results = cursor.fetchall()

#         # return results
#     return results
    
# def docnum(param):
#     extraxtTicket_filtrados = extraxtTicket.objects.filter(NumAtCard__contains=param)
          
#     for extract in extraxtTicket_filtrados:
#         DocNum = extract.DocNum
#         return DocNum


def createInsert():
    with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM v_etl2 ")
            results = cursor.fetchall()

        # return results
    return results
 
def vistaPrincipal():
    
    with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM v_etl2")
            results = cursor.fetchall()

        # return results
    return results    