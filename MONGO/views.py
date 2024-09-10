from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
# from django import models
from .models import TransacctionPago
from pymongo.errors import OperationFailure
from .models import SYS_PDETALLETRANS
from .models import SYS_PCOBROTRANS
from .models import SYS_PDETALLEDEVOL
from .models import SYS_PPAGOTANS
from django.http import JsonResponse
from pymongo.errors import ServerSelectionTimeoutError
from datetime import datetime, timedelta
from django.db import transaction
from pymongo import MongoClient
# from HANA.views import api_hana  # type: ignore
from .models import SYS_PTRANSACCIONES
from .models import SYS_PDEVOLUCIONES
from bson import ObjectId
from pymongo import mongo_client
import pymongo
from django.db import connection
import pymysql
from pymysql import connect, cursors
import re
import logging
import json
import requests
import pytz



# listo
def conectar_mongo():
    try:
        client = MongoClient('mongodb://abraham:abraham2023@192.168.10.200:27018/?authMechanism=DEFAULT')
        db = client['BridgeCentralBI']
        return db
    except ConnectionError as conn_error:
        raise conn_error
    except ServerSelectionTimeoutError as timeout_error:
        raise timeout_error
    
def conectar_sql():
    try:
        db = pymysql.connect(
            host='40.124.171.87',
            user= 'mobo',
            password= 'moboweb5226',
            database='consolidacion',
            cursorclass=cursors.DictCursor,
            autocommit=True
        )
        return db
    except Exception as e:
        logging.error("Error al conectar a la base de datos: sql %s",e)
        return None

def manejar_resultados(resultReturn):
    if resultReturn is True:
        return JsonResponse({"status": 201, "message": "Successfully exported data to MongoDB"}, status=201)
    elif resultReturn == "No data to process":
        return JsonResponse({"status": 204, "message": "No data to process"}, status=204)
    else:
        return JsonResponse({"status": 409, "message": "Error in the process of saving data to MongoDB: " + resultReturn}, status=409)

def manejar_error(error):
    return JsonResponse({'error eres este ?': str(error)})

def pipelineMongoETL():

    fecha_actual = datetime.now()
    fecha_formateada = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day)
    fecha_menos_10_dias = fecha_formateada - timedelta(days=10)

    pipeline = [
                    {
                        '$match': {
                        'storeCode': { '$in': ['304', '262', '026','031','016','813'] },
                        # 'trxNumber': 153,
                        'trxType': { '$in': ['Sale','Return'] },
                        'cancelFlag': False,
                        # 'beginDateTime': {
                        #     '$gte': fecha_inicio,
                        #     '$lte': fecha_formateada,
                        # }
                        }
                    },
                    {
                        '$lookup': {
                        'from': 'TransactionRetailPayment',
                        'localField': '_id',
                        'foreignField': 'transactionObjectId',
                        'as': 'formas_pago'
                        }
                    },
                    {
                        '$project': {
                        'venta_sk': '$uniqueTrxReference',
                        'venta_sk_n': '$trxNumber',
                        'priceListId': { '$arrayElemAt': ['$items.priceListId', 0] },
                        'sucursal': '$storeCode',
                        'caja': '$userName',
                        'numLine': '$items_.numLine',
                        'almacen': { '$concat': ['T', '$storeCode'] },
                        'hora24h': {
                            '$dateToString': {
                            'format': '%H:%m',
                            'date': '$endDateTime'
                            }
                        },
                        'ffecha': {
                            '$dateToString': {
                            'format': '%Y%m%d',
                            'date': '$endDateTime'
                            }
                        },
                        'horastr': {
                            '$dateToString': {
                            'format': '%H%m',
                            'date': '$endDateTime'
                            }
                        },
                        'codeSucursal': { '$concat': ['V000', '$storeCode'] },
                        'fecha_process': {
                            '$dateToString': {
                            'format': '%Y%m%d',
                            'date': '$beginDateTime'
                            }
                        },
                        'items_': {
                            '$map': {
                            'input': {
                                '$filter': {
                                'input': '$items',
                                'as': 'item',
                                'cond': {
                                    '$and': [
                                    { '$eq': ['$$item.voidedQuantity', 0] },
                                    { '$eq': ['$$item.voiding', False] }
                                    ]
                                }
                                }
                            },
                            'as': 'item',
                            'in': {
                                'sellerID': '$$item.sellerID',
                                'SKU': '$$item.item.internalCode',
                                'barcode':'$$item.posItemID',
                                'description':'$$item.item.description',
                                'quantity': {
                                    '$cond': {
                                        'if': {
                                            '$gte': [
                                                '$$item.voidedQuantity', 1
                                            ]
                                        }, 
                                        'then': {
                                            '$subtract': [
                                                '$$item.quantity', '$$item.voidedQuantity'
                                            ]
                                        }, 
                                        'else': '$$item.quantity'
                                    }
                                }, 
                                'priceWoVAT': '$$item.priceWithoutVAT',
                                'IVA': {
                                    '$cond': {
                                        'if': {
                                            '$gte': [
                                                '$$item.voidedQuantity', 1
                                            ]
                                        }, 
                                        'then': {
                                            '$subtract': [
                                                '$$item.remainingCustomerExtendedAmount', '$$item.remainingNetPriceWithoutDiscounts'
                                            ]
                                        }, 
                                        'else': '$$item.priceIvaAmount'
                                    }
                                }, 
                                'total_disc': '$$item.discountGrossAmount',
                                'precio_brutoSD': '$$item.grossUnitPrice',
                                'pnsd': '$$item.priceWithoutVAT',
                                'pncd': {'$add': ['$$item.discountGrossAmount', '$$item.priceWithoutVAT']}
                            }
                            }
                        },
                        'subtotal': { '$subtract': ['$paymentsTotal', '$ivaTotal'] },
                        'total': '$paymentsTotal',
                        'partyIdentifier': "$party.identifier",
                        'partyCode': "$party.code",
                        'formas_pago': {
                            '$map': {
                                'input': '$formas_pago',
                                'as': 'fp',
                                'in': {
                                    'fp_amount': '$$fp.netAmount',
                                    'change': '$$fp.change',
                                    'fp_code': '$$fp.tenderType.code',
                                    'fp_codeName': '$$fp.tenderType.codeName',
                                    'fopa': {
                                        '$cond': {
                                        'if': { '$eq': ["$$fp.tenderType.codeName", "CARD"] },
                                        'then': {
                                            '$concat': ["$$fp.tenderCode",
                                            {
                                                '$cond': {
                                                'if': {
                                                    '$in': ["$$fp.installments", ["1", "3", "6", "9"]]
                                                },
                                                'then': { '$concat': ["0", "$$fp.installments"] },
                                                'else': "$$fp.installments"
                                                }
                                            }
                                            ]
                                        },
                                        'else': {
                                            '$cond': {
                                            'if': {
                                                '$eq': ["$$fp.tenderType.codeName", "CASH"]
                                            },
                                            'then': "EFECTIVO",
                                            'else': 'null'
                                            }
                                        }
                                        }
                                    }
                                },
                            },
                        },
                        }
                    },
                    
                    { '$unset': '_id' },
                    {
                        '$unwind': {
                        'path': '$items_',
                        'preserveNullAndEmptyArrays': True,
                        'includeArrayIndex': 'numLine'
                        }
                    },
                    {
                        '$unwind': {
                        'path': '$formas_pago',
                        'preserveNullAndEmptyArrays': True
                        }
                    },
                    {
                        '$unwind': {
                        'path': '$promos',
                        'preserveNullAndEmptyArrays': True
                        }
                    }
        ]
    return pipeline

def craftMongo(request):
    # try:
        db = conectar_mongo()
        pipeline = pipelineMongoETL()

        result = list(db.Transaction.aggregate(pipeline))
        # return HttpResponse(result)
        resultReturn = saveDataMongo(result)
        return HttpResponse(resultReturn)
        if resultReturn :
            return HttpResponse("Se logro")
        else : 
            return HttpResponse("No se pudo guardar en mysql")
        
        

    # except (ConnectionError, ServerSelectionTimeoutError, OperationFailure) as error:
    #    return manejar_error(error)
    # except Exception as e:
    #     return manejar_error(e)    

def saveDataMongo(data):
    
    for item in data:
        # Intentar crear una instancia de TransacctionPago y guardarla en la base de datos
        transaccion_principal = TransacctionPago(
            # FolioSig=folio,
            venta_sk=item['venta_sk'],
            venta_sk_n=item['venta_sk_n'],
            priceListId=item['priceListId'],
            sucursal=item['sucursal'],
            caja=item['caja'],
            almacen=item['almacen'],
            hora24h=item['hora24h'],
            ffecha=item['ffecha'],
            horastr=item['horastr'],
            codeSucursal=item['codeSucursal'],
            fecha_process=item['fecha_process'],
            sellerID=item['items_']['sellerID'],
            SKU=item['items_']['SKU'],
            quantity=item['items_']['quantity'],
            priceWoVAT=item['items_']['priceWoVAT'],
            IVA=item['items_']['IVA'],
            total_disc=item['items_']['total_disc'],
            precio_brutoSD=item['items_']['precio_brutoSD'],
            subtotal=item['subtotal'],
            total=item['total'],
            fp_amount=item['formas_pago']['fp_amount'],
            cambio=item['formas_pago']['change'],
            fp_code=item['formas_pago']['fp_code'],
            fp_codeName=item['formas_pago']['fp_codeName'],
            partyCode=item.get('partyCode', ''),
            partyIdentifier=item.get('partyIdentifier', ''),
            description=item['items_']['description'],
            fopa=item['formas_pago']['fopa'],
            pncd=item['items_']['pncd'],
            barcode=item['items_'].get('barcode',''),
            NumLine=item['items_'].get('NumLine'),                      
        )
        try:
            with transaction.atomic():
                transaccion_principal.save(using='default')
                # return True
        except Exception as e:
            return HttpResponse(f'"Error" {e}')
            


        # if 'V' in str(venta_sk) or 'F' in str(venta_sk):
        #     if 'V' in str(venta_sk):
        #         pcobrotrans = SYS_PCOBROTRANS(          #VENDRA EN EL MODELO 
        #                 skComplet=str(ticketCons),
        #                 # venta_sk=str(venta_sk),       
        #                 guardado = 1,                   
        #             )
        #         pcobrotrans.save(using='default')
        #     elif 'F' in str(venta_sk):
        #         pdetalle = SYS_PDETALLETRANS(           #VENDRA DEL MODELO 
        #             skComplet=str(ticketCons),
        #             # venta_sk=str(venta_sk),       
        #             guardado = 1,                   
        #         )
        #         pdetalle.save(using='default')
        #         # SYS_PDETALLETRANS
        #         data = {
        #                 "FilterEq" : {
        #                     "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PTRANSACCIONES\" (\"Code\", \"Name\", \"U_SYS_HOCA\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_SUCU\", \"U_SYS_CAJA\", \"U_SYS_CAJE\", \"U_SYS_CLMO\", \"U_SYS_SONE\", \"U_SYS_MEMB\", \"U_SYS_AGEV\", \"U_SYS_NUDS\", \"U_SYS_NUSI\", \"U_SYS_USAU\", \"U_SYS_IMPU\", \"U_SYS_SUBT\", \"U_SYS_TOTT\", \"U_SYS_TOTN\", \"U_SYS_CAMB\", \"U_SYS_SALA\", \"U_SYS_COME\", \"U_SYS_TRAS\", \"U_SYS_VPUG\", \"U_SYS_SERV\", \"U_SYS_FACT\", \"U_SYS_CANC\", \"U_SYS_LINE\", \"U_SYS_CANE\", \"U_SYS_DEES\", \"U_SYS_TIPO\", \"U_SYS_ESRE\", \"U_SYS_CLAP\", \"U_SYS_TEAP\", \"U_SYS_COMA\", \"U_SYS_ESAP\", \"U_SYS_FPRO\", \"U_SYS_HPRO\", \"U_SYS_LIPE\", \"U_SYS_VSPC\", \"U_SYS_DECU\", \"U_SYS_DESB\", \"U_SYS_ ESRS\", \"U_SYS_FACD\", \"U_SYS_FOCU\", \"U_SYS_FOVI\", \"U_SYS_IDCE\", \"U_SYS_IDEI\", \"U_SYS_IDEP\", \"U_SYS_IDPU\", \"U_SYS_OCUP\", \"U_SYS_ PDCF\", \"U_SYS_ POCU\", \"U_SYS_ PROY\", \"U_SYS_SELE\", \"U_SYS_TDEI\", \"U_SYS_TPRO\", \"U_SYS_VEVT\", \"U_SYS_TPSI\", \"U_SYS_MOSI\", \"U_SYS_MESI\", \"U_SYS_TISI\", \"U_SYS_PUNT\", \"U_SYS_MAPA\", \"U_SYS_ORTR\", \"U_SYS_FOEX\") VALUES  (\'{skComplet}\',\'{venta_sk}\', \'{hora24h}\', \'{fecha_process}\', \'{horastr}\', \'{sucursal}\', \'{caja}\', \'{sellerID}\', \'{partyIdentifier}\', \'{codeSucursal}\', \'{partyCode}\', \'{sellerID}\', \'{docnumultimo}\', \'0\', \'-1\', \'{iva}\', \'{subtotal}\', {total}, {fp_amount}, {change}, \'0\', \'\', \'N\', \'Y\', \'N\', \'N\', \'N\', \'N\', \'N\', \'N\', \'{tipo_vent}\', \'N\', \'\', \'\', \'\', \'\', \'{fecha_process}\', \'{horastr}\', \'{priceListId}\', \'{tpp}\', \'0\', \'0\', \'N\', \'\', \'\', \'\', \'0\', \'0\', \'0\', \'0\', \'\', \'0\', \'0\', \'\', \'N\', \'0\', \'\', \'N\', \'X\', \'Y\', \'\', \'\', \'0\', \'N\',\'E\' \'{venta_sk_n}\')'
        #                 }
        #             }
        #         print(data)
        #         # SYS_PDETALLETRANS
        #         data = {
        #                 "FilterEq": {
        #                     "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDETALLETRANS\" (\"Code\", \"Name\", \"U_SYS_FOLT\", \"U_SYS_CODA\", \"U_SYS_CODB\", \"U_SYS_CUEN\", \"U_SYS_ALMA\", \"U_SYS_CENC\", \"U_SYS_PROY\", \"U_SYS_DESC\", \"U_SYS_SERV\", \"U_SYS_NUME\", \"U_SYS_CANT\", \"U_SYS_CANA\", \"U_SYS_PNSD\", \"U_SYS_PNCD\", \"U_SYS_IMPN\", \"U_SYS_PBSD\", \"U_SYS_PBCD\", \"U_SYS_IMPU\", \"U_SYS_IMPD\", \"U_SYS_IMCD\", \"U_SYS_FECH\", \"U_SYS_FECE\", \"U_SYS_UNBA\", \"U_SYS_GARA\", \"U_SYS_CANC\", \"U_SYS_TMIN\", \"U_SYS_CNPA\", \"U_SYS_IIMP\", \"U_SYS_PROR\", \"U_SYS_PUNT\", \"U_SYS_POPU\", \"U_SYS_SERV\") VALUES (\'{skComplet}\',\'{venta_sk}\', \'{venta_sk}\', \'{sku}\', \'{barcode}\', \'\', \'{sucursal}\', \'\', \'\', \'{description}\', \'\', \'\', \'{quantity}\', \'0\', \'{priceWoVAT}\', \'{pncd}\', \'IMPN\', \'{precio_brutoSD}\', \'{priceWoVAT}\', \'{iva}\', \'0\', \'{total_disc}\', \'{fecha_process}\', \'\', \'N\', \'N\',\'N\', \'IN\', \'0\', \'\', \'0\',\'0\',\'0\',\'N\')'
        #                 }
        #             }
        #         print(data)
        #         # tabla de @SYS_PCOBROTRANS
        #         data = {
        #                 "FilterEq": {
        #                         "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PCOBROTRANS\"(\"Code\",\"Name\", \"U_SYS_HOCA\", \"U_SYS_NUME\", \"U_SYS_NUMC\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_FOLT\", \"U_SYS_BANC\", \"U_SYS_NUMT\", \"U_SYS_AUTT\", \"U_SYS_VIGT\", \"U_SYS_FOPA\", \"U_SYS_ANTI\", \"U_SYS_REFE\", \"U_SYS_MONP\", \"U_SYS_MONN\", \"U_SYS_MONB\", \"U_SYS_INRE\", \"U_SYS_CCTP\", \"U_SYS_TICA\", \"U_SYS_MONE\") VALUES (\'{skComplet}\', \'{venta_sk}\', \'{hora24h}\',\'{sellerID}\',\'0\',\'{fecha_process}\',\'{horastr}\',\'{skComplet}\',\'\',\'\',\'\',\'\',\'{fopa}\',\'\',\'\',\'{total}\', \'{total_disc}\', \'{precio_brutoSD}\',\'Y\', \'\',\'0\', \'0\')'
        #                     }
        #             }
        #         print(data)
        # elif 'D' in str(venta_sk) or 'N' in str(venta_sk):
        #     if 'D' in str(venta_sk):
        #         ppagotrans = SYS_PPAGOTANS(             #VENDRA DEL MODELO 
        #             skComplet=str(ticketCons),
        #             venta_sk=str(venta_sk),       
        #             guardado = 1,                   
        #         )
        #         ppagotrans.save(using='default')
        #     elif 'N' in str(venta_sk):
        #         pdetalledevol = SYS_PDETALLEDEVOL(         #VENDRA DEL MODELO 
        #             skComplet=str(ticketCons),
        #             venta_sk=str(venta_sk),       
        #             guardado = 1,                   
        #         )
        #         pdetalledevol.save(using='default')
                
        #         # tabla @SYS_PDEVOLUCIONES
        #         data = {
        #             "FilterEq": {
        #                     "Qurey": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDEVOLUCIONES\" (\"Code\", \"Name\", \"U_SYS_AGEV\", \"U_SYS_CAJA\", \"U_SYS_CAJE\", \"U_SYS_CAMB\", \"U_SYS_CLMO\", \"U_SYS_COME\", \"U_SYS_CORE\", \"U_SYS_DESB\", \"U_SYS_DESC\", \"U_SYS_DIDE\", \"U_SYS_FACD\", \"U_SYS_FECH\", \"U_SYS_FOTR\", \"U_SYS_FPRO\", \"U_SYS_HOCA\", \"U_SYS_HORA\", \"U_SYS_HPRO\", \"U_SYS_IDCE\", \"U_SYS_IDEI\", \"U_SYS_IDPU\", \"U_SYS_IMPO\", \"U_SYS_MEMB\", \"U_SYS_MESI\", \"U_SYS_MODE\", \"U_SYS_MOSI\", \"U_SYS_NUDS\", \"U_SYS_PDCF\", \"U_SYS_PROY\", \"U_SYS_PUDE\", \"U_SYS_SELE\", \"U_SYS_SERV\", \"U_SYS_SONE\", \"U_SYS_SUCU\", \"U_SYS_TISI\", \"U_SYS_TOTN\", \"U_SYS_TPSI\", \"U_SYS_TRAS\", \"U_SYS_VSPC\", \"U_SYS_DNXM\", \"U_SYS_VENC\", \"U_SYS_FOAL\", \"U_SYS_ORTR\", \"U_SYS_FOEX\") VALUES (\'{skComplet}\',\'{venta_sk}\', \'{sellerID}\', \'{caja}\', {sellerID}, \'{change}\', \'{partyIdentifier}\', \'\',\'\', \'0\',\'{description}\',\'0\',\'\',\'{fecha_process}\', \'0\', \'{fecha_process}\', \'{horastr}\', \'{horastr}\', \'{horastr}\', \'0\', \'0\', \'0\', \'{fp_amount}\', \'{partyCode}\', \'\', \'\', \'Y\', \'{docnumultimo}\', \'0\', \'\', \'0\', \'N\', \'N\', \'{sellerID}\', \'{sucursal}\', \'\', \'{fp_amount}\', \'X\', \'N\', \'{tpp}\', \'N\', \'N\', \'\', \'E\', \'{venta_sk_n}\')'
        #                     }
        #                 }
        #         print(data)
        #         # tabla @SYS_PDETALLEDEVOL
        #         data = {
        #             "FilterEq": {
        #                 "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDETALLEDEVOL\"(\"Code\", \"Name\", \"U_SYS_ALMA\", \"U_SYS_CANT\", \"U_SYS_CENC\", \"U_SYS_CODA\", \"U_SYS_CODB\", \"U_SYS_CUEN\", \"U_SYS_DCTO\", \"U_SYS_DESC\", \"U_SYS_FECH\", \"U_SYS_FOLT\", \"U_SYS_IDCE\", \"U_SYS_IIMP\", \"U_SYS_IMCD\", \"U_SYS_IMPD\", \"U_SYS_IMPN\", \"U_SYS_IMPU\", \"U_SYS_MDCF\", \"U_SYS_NUME\", \"U_SYS_PBCD\", \"U_SYS_PBSD\", \"U_SYS_PDCF\", \"U_SYS_PNCD\", \"U_SYS_PNSD\", \"U_SYS_PAPU\", \"U_SYS_PROY\", \"U_SYS_PUNT\", \"U_SYS_SERV\", \"U_SYS_TDEI\", \"U_SYS_TMIN\", \"U_SYS_UNBA\") VALUES (\'{skComplet}\', \'{venta_sk}\',\'{sucursal}\', \'{quantity}\', \'\', \'{sku}\' , \'{barcode}\', \'\', \'0\', \'{description}\', \'{fecha_process}\', \'{venta_sk}\',\'0\',\'\',\'{total_disc}\', \'0\', \'\', \'{iva}\', \'0\', \'\', \'{priceWoVAT}\', \'{precio_brutoSD}\', \'0\',\'{subtotal}\', \'{iva}\', \'0\', \'\', \'0\', \'N\',\'{sellerID}\', \'IN\', \'N\')'
        #                     }
        #             }
        #         print(data)
        #         # tabla @SYS_PPAGOTANS
        #         data = {
        #                 "FilterEq": {
        #                     "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PPAGOTANS\"(\"Code\", \"Name\", \"U_SYS_HOCA\", \"U_SYS_NUME\", \"U_SYS_NUMC\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_FOLT\", \"U_SYS_BANC\",\"U_SYS_NUMT\", \"U_SYS_AUTT\", \"U_SYS_VIGT\", \"U_SYS_FOPA\", \"U_SYS_REFE\", \"U_SYS_MONP\", \"U_SYS_MONN\",\"U_SYS_MONB\", \"U_SYS_CCTP\") VALUES (\'{skComplet}\', \'{venta_sk}\', \'{fecha_process}\', \'0\', \'0\', \'{fecha_process}\', \'{fecha_process}\', \'{skComplet}\', \'\', \'\', \'\', \'\', \'{fopa}\', \'\', \'{subtotal}\', \'{total_disc}\',\'{precio_brutoSD}\', \'\')'
        #                 }
        #         }
        #         print(data)
                
        # else:
        #     print("Otra acción")

# funcion solo de prueba para probar conectarme a napse
# def test_connection():
#     client =  pymongo.MongoClient('mongodb://moboread:w6vbhXT@192.168.10.24:27018/?authMechanism=SCRAM-SHA-1')
#     try:
#         db_name = client.list_database_names()
#         print("conexion exitosa.Base de datos disponible", db_name)
#     except Exception as e:
#         print("Error al conectar con la base", e)
# test_connection()


# Napse extraccion 
# funciones que le robe a abraham xD
def GetToMongo(username, password, hostname, port,database, collection, authMechanism ):
    try:
        uri = f"mongodb://{username}:{password}@{hostname}:{port}/?authSource={database}&authMechanism={authMechanism}"
        mongo_uri = uri
        client = MongoClient(mongo_uri)
        db = client[database]
        collection_db = db[collection]
        return collection_db
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")


def aggregateMongo(pipelinee,collection):
    return collection.aggregate(pipelinee)

# funcion para convertir a json la consulta
def convertir_json(documento):
    for clave, valor in documento.items():
        if isinstance(valor, dict):
            convertir_json(valor)
        elif isinstance(valor, list):
            for elemento in valor:
                convertir_json(elemento)
        elif isinstance(valor, ObjectId):
            documento[clave] = str(valor)
    documento.pop('_id', None)

def format_fecha(documento):
    documento['merged_data']['data']['ffecha'] = '{}-{}-{}'.format(
        documento['merged_data']['data']['ffecha'][:4],
        documento['merged_data']['data']['ffecha'][4:6],
        documento['merged_data']['data']['ffecha'][6:]
    )
    documento['merged_data']['data']['fecha_process'] = documento['merged_data']['data']['ffecha']
    return documento

def newmongoV2(request):
    mongo_host = "192.168.10.24"
    mongo_port = 27018
    database_name = "bridgeCentral"
    collection_name = "Transaction"
    username = "moboread"
    authMechanism= "SCRAM-SHA-1"
    password = "w6vbhXT"

    fecha_inicio = "2024-01-01"
    fecha_fin = "2024-01-31"

    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")

    gmt_minus_6 = pytz.timezone('America/Mexico_City')
    fecha_inicio_dt = gmt_minus_6.localize(fecha_inicio_dt)
    fecha_fin_dt = gmt_minus_6.localize(fecha_fin_dt) + timedelta(days=1) - - timedelta(milliseconds=1)

    pipelinee = [
    {
        '$match': {
            'storeCode': {'$in':['304','262','031','016','813','327','112','829','824','830','815','811','822','828','820','812','816','827','818','819','821','823','825','826','338']},

            'trxType':{'$in':['Return','Sale']},
            'cancelFlag': False,
            'paid':True,
            'trxStatus':'ok',
            'beginDateTime': {
              '$gte': fecha_inicio_dt, 
                '$lte': fecha_fin_dt
            },
        }
    }, 
    {
        '$lookup': {
            'from': 'TransactionRetailPayment', 
            'localField': '_id', 
            'foreignField': 'transactionObjectId', 
            'as': 'formas_pago'
        }
    },  
    {
        '$project': {
            'venta_sk': '$uniqueTrxReference', 
            'venta_sk_n': '$trxNumber', 
            'ffecha': {
                '$dateToString': {
                    'format': '%Y%m%d', 
                    'date': '$endDateTime',
                    'timezone':'America/Mexico_City'
                }
            }, 
            'hora': {
                '$dateToString': {
                    'format': '%H:%m', 
                    'date': '$endDateTime',
                    'timezone':'America/Mexico_City'
                }
            }, 
            'sucursal': '$storeCode', 
            'tipo_venta': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$trxType', 'Sale'
                        ]
                    }, 
                    'then': 'Venta', 
                    'else': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$trxType', 'Return'
                                ]
                            }, 
                            'then': 'Devolucion', 
                            'else': 'NI'
                        }
                    }
                }
            }, 
            'items_': {
                '$map': {
                    'input':  {
                        '$filter': {
                            'input': '$items', 
                            'as': 'item', 
                            'cond': {
                                '$eq': [
                                    '$$item.voiding', False
                                ]
                            }
                        }
                    }, 
                    'as': 'item', 
                    'in': {
                        'quantity': {
                            '$cond': {
                                'if': {
                                    '$gte': [
                                        '$$item.voidedQuantity', 1
                                    ]
                                }, 
                                'then': {
                                    '$subtract': [
                                        '$$item.quantity', '$$item.voidedQuantity'
                                    ]
                                }, 
                                'else': '$$item.quantity'
                            }
                        }, 
                        'priceWoVAT': '$$item.priceWithoutVAT', 
                        'IVA': {
                            '$cond': {
                                'if': {
                                    '$gte': [
                                        '$$item.voidedQuantity', 1
                                    ]
                                }, 
                                'then': {
                                    '$subtract': [
                                        '$$item.remainingCustomerExtendedAmount', '$$item.remainingNetPriceWithoutDiscounts'
                                    ]
                                }, 
                                'else': '$$item.priceIvaAmount'
                            }
                        },
                        'total_disc': '$$item.discountGrossAmount', 
                        'gross_up': '$$item.grossUnitPrice', 
                        'balance': {
                            '$add': [
                                '$$item.discountTotal', '$$item.grossUnitPrice'
                            ]
                        }, 
                         'importe_c_desc': {
                            '$cond': {
                                'if': {
                                    '$gte': [
                                        '$$item.voidedQuantity', 1
                                    ]
                                }, 
                                'then': {
                                    '$add': [
                                        '$$item.discountsWithPromoTotal', '$$item.remainingCustomerExtendedAmount'
                                    ]
                                },
                                'else': '$$item.customerOriginalExtendedNetPrice'
                            }
                        }
                    }
                }
            },
             'subtotal': {
                '$round': [
                    {
                        '$subtract': [
                            '$positiveGross', {
                                '$add': [
                                    '$negativeGross', '$ivaTotal'
                                ]
                            }
                        ]
                    }, 2
                ]
            }, 
            'total': {
                '$round': [
                    {
                        '$subtract': [
                            '$positiveGross', '$negativeGross'
                        ]
                    }, 2
                ]
            },
            'formas_pago': {
                '$map': {
                    'input': '$formas_pago', 
                    'as': 'fp', 
                    'in': {
                        'fp_id': '$$fp.tenderName', 
                        'fp_amount': '$$fp.netAmount', 
                        'fp_installments': {
                            '$ifNull': [
                                '$$fp.installments', 1
                            ]
                        }, 
                        'fp_bank': '$$fp.planDescriptor', 
                        'fp_date': {
                            '$dateToString': {
                                'format': '%Y%m%d', 
                                'date': '$$fp.beginDateTime',
                                'timezone':'America/Mexico_City'
                            }
                        },
                        'fp_auth_code': '$$fp.cardAuthorizationCode', 
                        'fp_ref_code': '$$fp.cardLotNumber',
                        'fopa': {
                            '$cond': {
                                'if': {
                                    '$eq': [
                                        '$$fp.tenderType.codeName', 'CARD'
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '$$fp.tenderCode', {
                                            '$cond': {
                                                'if': {
                                                    '$in': [
                                                        '$$fp.installments', [
                                                            '1', '3', '6', '9'
                                                        ]
                                                    ]
                                                }, 
                                                'then': {
                                                    '$concat': [
                                                        '0', '$$fp.installments'
                                                    ]
                                                }, 
                                                'else': '$$fp.installments'
                                            }
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$cond': {
                                        'if': {
                                            '$eq': [
                                                '$$fp.tenderType.codeName', 'CASH'
                                            ]
                                        }, 
                                        'then': 'EFECTIVO', 
                                        'else': {
                                            '$cond': {
                                                'if': {
                                                    '$eq': [
                                                        '$$fp.tenderType.codeName', 'COUPON'
                                                    ]
                                                },
                                                'then': 'Kueski Pay',
                                                'else': {
                                                    '$cond': {
                                                        'if': {
                                                            '$eq': [
                                                                '$$fp.tenderName', 'Transferencia BBVA'
                                                            ]
                                                        },
                                                        'then': 'TRANS01',
                                                        'else': 'TRANS02'
                                                    },
                                                }
                                            },
                                        },
                                    }
                                },
                            }
                        }
                    }
                }
            },
        }
    }, 
    {
        '$group':{
            '_id':{
                'ffecha': '$ffecha',
                'sucursal': '$sucursal'
            },
            'data': {'$push': '$$ROOT'}
        }
    },
    {
        '$group':{
            '_id': None,
            'merged_data': {'$push': '$$ROOT'}
        }
    },
    {
        '$project':{
            '_id': 0,
            'merged_data': 1
        }
    },
    {
        '$unwind': '$merged_data'
    },
    {
        '$unwind': '$merged_data.data'
    },
    {
        '$unwind':{
            'path': '$merged_data.data.items_',
            'preserveNullAndEmptyArrays': True,
            'includeArrayIndex': 'numLine'
        }
    },
    {
        '$unwind':{
            'path': '$merged_data.data.items_.discounts',
            'preserveNullAndEmptyArrays': True
        }
    },
    {
        '$unwind':{
            'path': '$merged_data.data.formas_pago',
            'preserveNullAndEmptyArrays': True
        }
    },
    {
        '$unwind':{
            'path': '$merged_data.data.promos',
            'preserveNullAndEmptyArrays': True
        }
    },
]
    
    try:
        collection = GetToMongo(username, password, mongo_host, mongo_port, database_name, collection_name, authMechanism)
        res = aggregateMongo(pipelinee, collection)
        result_list = list(res)

        if result_list:
            result_list = [format_fecha(documento) for  documento in result_list]
            for documento in result_list: 
                if '_id' in documento['merged_data']:
                    del documento['merged_data']['_id']
                # if 'data' in documento['merged_data'] and '_id' in documento['merged_data']['data']:
                #     del documento['merged_data']['data']['_id']
                print("docuemento",documento)
                datos_filtrados = filtrar_datos(documento)
                # NapseCB(datos_filtrados)
                # print("web",datos_filtrados)
            return JsonResponse(datos_filtrados, safe=False)
        else:
            return JsonResponse([], safe=False)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")
    

def filtrar_datos(documento):
    datos_filtrados = {
        "venta_sk": documento["merged_data"]["data"]["venta_sk"], #1
        "venta_sk_n": documento["merged_data"]["data"]["venta_sk_n"], #2
        "ffecha": documento["merged_data"]["data"]["ffecha"], #3
        "hora": documento["merged_data"]["data"]["hora"], #4
        "sucursal": documento["merged_data"]["data"]["sucursal"], #5
        "tipo_venta": documento["merged_data"]["data"]["tipo_venta"], #6
        "subtotal": documento["merged_data"]["data"]["subtotal"],#7
        "total": documento["merged_data"]["data"]["total"],#8
        "fp_id": documento["merged_data"]["data"]["formas_pago"]["fp_id"],#9
        "fp_amount": documento["merged_data"]["data"]["formas_pago"]["fp_amount"],#10
        "fp_installments": documento["merged_data"]["data"]["formas_pago"]["fp_installments"],#11
        "fopa": documento["merged_data"]["data"]["formas_pago"]["fopa"]#12
    }
    print("filtrar datos",datos_filtrados)
    return datos_filtrados

def NapseCB(datos_filtrados):
    conexion = conectar_sql()

    try:
        cursor = conexion.cursor()
        query = """
        INSERT INTO NapseCB(Venta_sk, Venta_sk_n, Ffecha, Hora, Sucursal, Tipo_venta, Subtotal, Total, Fp_id, Fp_amount, Fp_installments, Fopa)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (datos_filtrados["venta_sk"], 
                               datos_filtrados["venta_sk_n"], 
                               datos_filtrados["ffecha"], 
                               datos_filtrados["hora"],
                               datos_filtrados["sucursal"],
                               datos_filtrados["tipo_venta"],
                               datos_filtrados["subtotal"],
                               datos_filtrados["total"],
                               datos_filtrados["fp_id"],
                               datos_filtrados["fp_amount"],
                               datos_filtrados["fp_installments"],
                               datos_filtrados["fopa"]))
        conexion.commit()
        cursor.close()
    except Exception as e:
        conexion.rollback()
        cursor.close()
        conexion.close()
        raise e