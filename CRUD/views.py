from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import libro
from .models import TransacctionPago
from .models import transaccionHana
from .models import fichasdeposito
from .models import FolioSiguientePorSucursal
from .models import SYS_PTRANSACCIONES
from .models import SYS_PDETALLETRANS
from .models import SYS_PCOBROTRANS
from .models import SYS_PDEVOLUCIONES
from .models import SYS_PDETALLEDEVOL
from .models import SYS_PPAGOTANS
from .models import extraxtTicket
from .forms import libroForm
from datetime import datetime
from bson import ObjectId
from django.http import JsonResponse
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from djongo import models
from datetime import datetime, timedelta
from django.db import connection
from django.db import transaction


import re

import logging
import pdb
import json
import requests


# vistas para pruebas de crud
def inicio(request):
    return render(request, "paginas/inicio.html")

def nosotros(request):
    return render(request, "paginas/nosotros.html")

def libros(request):
    libros = libro.objects.all()
    return render(request, "libros/index.html" , {'libros':libros})

def crear(request):
    formulario = libroForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('libros')
    return render(request, "libros/crear.html", {'formulario':formulario})

def editar(request, id):
    libro_ojetc = libro.objects(id=id)
    formulario = libroForm(request.POST or None, request.FILES or None,instance=libro_ojetc)
    if formulario.is_valid() and request.POST:
        formulario.save()
        return redirect('libros')
    return render(request, "libros/editar.html", {'formulario':formulario})

def eliminar(request, id):
    libro_obj = libro.objects(id=id)
    libro_obj.delete()
    return redirect('libros')


# consulta para consulidacion
# inico de funciones para consolidacion napse
def consultamobonet(request):
    limit = 11  # Número de registros a mostrar
    data_list = fichasdeposito.objects.using('mobonet').all()[:limit]  # Obtener los primeros 'limit' registros
    return render(request, 'extract/mobonet.html', {'data_list': data_list})
  
def apihana(request):
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
  
def consultamongo():
    try:
        client = MongoClient('mongodb://abraham:abraham2023@192.168.10.200:27018/?authMechanism=DEFAULT')
        db = client['BridgeCentralBI']
        
        fecha_inicio = datetime(2023, 2, 1)
        fecha_fin = datetime(2023, 11, 30)
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
         
        # Obtener los documentos de la colección "Transaction" y convertir los ObjectId a cadenas de texto
        result = list(db.Transaction.aggregate(pipeline))
        resultReturn = saveDataMongo(result)
        if resultReturn is True:
            return JsonResponse({"status": 201, "message": "Successfully exported data to MongoDB"}, status=201)
        elif resultReturn == "No data to process":
            return JsonResponse({"status": 204, "message": "No data to process"}, status=204)
        else:
            return JsonResponse({"status": 409, "message": "Error in the process of saving data to MongoDB: " + result_return}, status=409)

    except ConnectionError as conn_error:
        # Maneja errores de conexión a MongoDB
        return JsonResponse({'error': f"Error de conexión a MongoDB: {str(conn_error)}"})

    except ServerSelectionTimeoutError as timeout_error:
        # Maneja errores de tiempo de espera de conexión
        return JsonResponse({'error': f"Tiempo de espera agotado para conectar a MongoDB: {str(timeout_error)}"})

    except Exception as e:
        # Maneja otras excepciones generales
        return JsonResponse({'error': str(e)})
    
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
            numLine=item['numLine'],
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
            change=item['formas_pago']['change'],
            fp_code=item['formas_pago']['fp_code'],
            fp_codeName=item['formas_pago']['fp_codeName'],
            partyCode=item.get('partyCode', ''),
            partyIdentifier=item.get('partyIdentifier', ''),
            description=item['items_']['description'],
            fopa=item['formas_pago']['fopa'],
            pncd=item['items_']['pncd'],
            barcode=item['items_'].get('barcode',''),                          
        )
        try:
            with transaction.atomic():
                transaccion_principal.save(using='default')
                return True
        except Exception as e:
            return HttpResponse(f'"Error" {e}')
            

def extract(request):
    fecha_actual = datetime.now()
    regreso = extractDataDocNum(fecha_actual)

    if regreso:
        return render(request, "extract/hana.html", {'result': "Se logró"})
    else:
        return HttpResponse("No se logró")

def extractDataDocNum(fecha_actual):
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
        
def etl(request):
    transactions = createInsert()

    for transaction  in transactions :
        venta_sk = transaction[1],
        venta_sk_n = transaction[2],
        priceListId = transaction[3],
        sucursal = transaction[4],
        caja = transaction[5],
        almacen = transaction[6],
        hora24h = transaction[7],
        ffecha = transaction[8],
        horastr = transaction[9],
        codeSucursal = transaction[10],
        fecha_process = transaction[11],
        sellerID = transaction[12],
        sku = transaction[13],
        quantity = transaction[14],
        priceWoVAT = transaction[15],
        iva = transaction[16],
        total_disc = transaction[17],
        precio_brutoSD = transaction[18],
        subtotal = transaction[19],
        total = transaction[20],
        fp_amount = transaction[21],
        change = transaction[22],
        fp_code = transaction[23],
        fp_codeName = transaction[24],
        partyCode = transaction[25],
        partyIdentifier = transaction[26],
        fopa = transaction[27],
        FolioSig = transaction[28],
        barcode = transaction[29],
        description = transaction[30],
        pncd = transaction[31],
        DocNum2 = transaction[32],
        tipo = transaction[33],
        RowNumber = transaction[34],
        ticket = transaction[35],
        consecutivo = transaction[36],
        ticketCons = transaction[37],
    
        tipo_vent = 'F'
        factura = 'N'
        tpp = 'N'
        # return HttpResponse(venta_sk)
        
        # # Validaciones
        # if 'F' in venta_sk:
        # elif 'V' in venta_sk:
        #     tipo_vent = 'V'
            
        # if 'F' in venta_sk:
        # elif 'V' in venta_sk:
        #     factura = 'N'
            
        # if re.match(r'^TPP', sku):
        #     tpp = 'P'
        # else:
        #     tpp = 'N'
    
    # ultmimo = createInsert(venta_sk)
    # docnumultimo = docnum(venta_sk)
    # # print(ultimo)
    # # return HttpResponse(ultmimo)    

    # mapeo_resultados = []

    # for resultado in ultmimo:
    #     mapeo_resultado = {
    #         "venta_sk": resultado[6],
    #         "consecutivo": resultado[5],
    #         "FolioSig": resultado[3],
    #     }
        
    #     mapeo_resultados.append(mapeo_resultado)

        # ticketCons = 0
        # # Itera a través de mapeo_resultados y suma los valores
        # for mapeo_resultado in mapeo_resultados:
    # ticketCons = sum(int(resultado['consecutivo']) + int(resultado['FolioSig']) for resultado in mapeo_resultados)

    # Calcula skComplet después de calcular la suma total
    # skComplet = mapeo_resultados[0]['venta_sk'] + str(ticketCons)
        
        # return HttpResponse(mapeo_resultado['venta_sk'])

        if 'V' in str(venta_sk) or 'F' in str(venta_sk):
            if 'V' in str(venta_sk):
                pcobrotrans = SYS_PCOBROTRANS(
                        skComplet=str(ticketCons),
                        # venta_sk=str(venta_sk),       
                        guardado = 1,                   
                    )
                pcobrotrans.save(using='default')
            elif 'F' in str(venta_sk):
                pdetalle = SYS_PDETALLETRANS(
                    skComplet=str(ticketCons),
                    # venta_sk=str(venta_sk),       
                    guardado = 1,                   
                )
                pdetalle.save(using='default')
                # SYS_PDETALLETRANS
                data = {
                        "FilterEq" : {
                            "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PTRANSACCIONES\" (\"Code\", \"Name\", \"U_SYS_HOCA\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_SUCU\", \"U_SYS_CAJA\", \"U_SYS_CAJE\", \"U_SYS_CLMO\", \"U_SYS_SONE\", \"U_SYS_MEMB\", \"U_SYS_AGEV\", \"U_SYS_NUDS\", \"U_SYS_NUSI\", \"U_SYS_USAU\", \"U_SYS_IMPU\", \"U_SYS_SUBT\", \"U_SYS_TOTT\", \"U_SYS_TOTN\", \"U_SYS_CAMB\", \"U_SYS_SALA\", \"U_SYS_COME\", \"U_SYS_TRAS\", \"U_SYS_VPUG\", \"U_SYS_SERV\", \"U_SYS_FACT\", \"U_SYS_CANC\", \"U_SYS_LINE\", \"U_SYS_CANE\", \"U_SYS_DEES\", \"U_SYS_TIPO\", \"U_SYS_ESRE\", \"U_SYS_CLAP\", \"U_SYS_TEAP\", \"U_SYS_COMA\", \"U_SYS_ESAP\", \"U_SYS_FPRO\", \"U_SYS_HPRO\", \"U_SYS_LIPE\", \"U_SYS_VSPC\", \"U_SYS_DECU\", \"U_SYS_DESB\", \"U_SYS_ ESRS\", \"U_SYS_FACD\", \"U_SYS_FOCU\", \"U_SYS_FOVI\", \"U_SYS_IDCE\", \"U_SYS_IDEI\", \"U_SYS_IDEP\", \"U_SYS_IDPU\", \"U_SYS_OCUP\", \"U_SYS_ PDCF\", \"U_SYS_ POCU\", \"U_SYS_ PROY\", \"U_SYS_SELE\", \"U_SYS_TDEI\", \"U_SYS_TPRO\", \"U_SYS_VEVT\", \"U_SYS_TPSI\", \"U_SYS_MOSI\", \"U_SYS_MESI\", \"U_SYS_TISI\", \"U_SYS_PUNT\", \"U_SYS_MAPA\", \"U_SYS_ORTR\", \"U_SYS_FOEX\") VALUES  (\'{skComplet}\',\'{venta_sk}\', \'{hora24h}\', \'{fecha_process}\', \'{horastr}\', \'{sucursal}\', \'{caja}\', \'{sellerID}\', \'{partyIdentifier}\', \'{codeSucursal}\', \'{partyCode}\', \'{sellerID}\', \'{docnumultimo}\', \'0\', \'-1\', \'{iva}\', \'{subtotal}\', {total}, {fp_amount}, {change}, \'0\', \'\', \'N\', \'Y\', \'N\', \'N\', \'N\', \'N\', \'N\', \'N\', \'{tipo_vent}\', \'N\', \'\', \'\', \'\', \'\', \'{fecha_process}\', \'{horastr}\', \'{priceListId}\', \'{tpp}\', \'0\', \'0\', \'N\', \'\', \'\', \'\', \'0\', \'0\', \'0\', \'0\', \'\', \'0\', \'0\', \'\', \'N\', \'0\', \'\', \'N\', \'X\', \'Y\', \'\', \'\', \'0\', \'N\',\'E\' \'{venta_sk_n}\')'
                        }
                    }
                print(data)
                # SYS_PDETALLETRANS
                data = {
                        "FilterEq": {
                            "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDETALLETRANS\" (\"Code\", \"Name\", \"U_SYS_FOLT\", \"U_SYS_CODA\", \"U_SYS_CODB\", \"U_SYS_CUEN\", \"U_SYS_ALMA\", \"U_SYS_CENC\", \"U_SYS_PROY\", \"U_SYS_DESC\", \"U_SYS_SERV\", \"U_SYS_NUME\", \"U_SYS_CANT\", \"U_SYS_CANA\", \"U_SYS_PNSD\", \"U_SYS_PNCD\", \"U_SYS_IMPN\", \"U_SYS_PBSD\", \"U_SYS_PBCD\", \"U_SYS_IMPU\", \"U_SYS_IMPD\", \"U_SYS_IMCD\", \"U_SYS_FECH\", \"U_SYS_FECE\", \"U_SYS_UNBA\", \"U_SYS_GARA\", \"U_SYS_CANC\", \"U_SYS_TMIN\", \"U_SYS_CNPA\", \"U_SYS_IIMP\", \"U_SYS_PROR\", \"U_SYS_PUNT\", \"U_SYS_POPU\", \"U_SYS_SERV\") VALUES (\'{skComplet}\',\'{venta_sk}\', \'{venta_sk}\', \'{sku}\', \'{barcode}\', \'\', \'{sucursal}\', \'\', \'\', \'{description}\', \'\', \'\', \'{quantity}\', \'0\', \'{priceWoVAT}\', \'{pncd}\', \'IMPN\', \'{precio_brutoSD}\', \'{priceWoVAT}\', \'{iva}\', \'0\', \'{total_disc}\', \'{fecha_process}\', \'\', \'N\', \'N\',\'N\', \'IN\', \'0\', \'\', \'0\',\'0\',\'0\',\'N\')'
                        }
                    }
                print(data)
                # tabla de @SYS_PCOBROTRANS
                data = {
                        "FilterEq": {
                                "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PCOBROTRANS\"(\"Code\",\"Name\", \"U_SYS_HOCA\", \"U_SYS_NUME\", \"U_SYS_NUMC\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_FOLT\", \"U_SYS_BANC\", \"U_SYS_NUMT\", \"U_SYS_AUTT\", \"U_SYS_VIGT\", \"U_SYS_FOPA\", \"U_SYS_ANTI\", \"U_SYS_REFE\", \"U_SYS_MONP\", \"U_SYS_MONN\", \"U_SYS_MONB\", \"U_SYS_INRE\", \"U_SYS_CCTP\", \"U_SYS_TICA\", \"U_SYS_MONE\") VALUES (\'{skComplet}\', \'{venta_sk}\', \'{hora24h}\',\'{sellerID}\',\'0\',\'{fecha_process}\',\'{horastr}\',\'{skComplet}\',\'\',\'\',\'\',\'\',\'{fopa}\',\'\',\'\',\'{total}\', \'{total_disc}\', \'{precio_brutoSD}\',\'Y\', \'\',\'0\', \'0\')'
                            }
                    }
                print(data)
        elif 'D' in str(venta_sk) or 'N' in str(venta_sk):
            if 'D' in str(venta_sk):
                ppagotrans = SYS_PPAGOTANS(
                    skComplet=str(ticketCons),
                    venta_sk=str(venta_sk),       
                    guardado = 1,                   
                )
                ppagotrans.save(using='default')
            elif 'N' in str(venta_sk):
                pdetalledevol = SYS_PDETALLEDEVOL(
                    skComplet=str(ticketCons),
                    venta_sk=str(venta_sk),       
                    guardado = 1,                   
                )
                pdetalledevol.save(using='default')
                
                # tabla @SYS_PDEVOLUCIONES
                data = {
                    "FilterEq": {
                            "Qurey": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDEVOLUCIONES\" (\"Code\", \"Name\", \"U_SYS_AGEV\", \"U_SYS_CAJA\", \"U_SYS_CAJE\", \"U_SYS_CAMB\", \"U_SYS_CLMO\", \"U_SYS_COME\", \"U_SYS_CORE\", \"U_SYS_DESB\", \"U_SYS_DESC\", \"U_SYS_DIDE\", \"U_SYS_FACD\", \"U_SYS_FECH\", \"U_SYS_FOTR\", \"U_SYS_FPRO\", \"U_SYS_HOCA\", \"U_SYS_HORA\", \"U_SYS_HPRO\", \"U_SYS_IDCE\", \"U_SYS_IDEI\", \"U_SYS_IDPU\", \"U_SYS_IMPO\", \"U_SYS_MEMB\", \"U_SYS_MESI\", \"U_SYS_MODE\", \"U_SYS_MOSI\", \"U_SYS_NUDS\", \"U_SYS_PDCF\", \"U_SYS_PROY\", \"U_SYS_PUDE\", \"U_SYS_SELE\", \"U_SYS_SERV\", \"U_SYS_SONE\", \"U_SYS_SUCU\", \"U_SYS_TISI\", \"U_SYS_TOTN\", \"U_SYS_TPSI\", \"U_SYS_TRAS\", \"U_SYS_VSPC\", \"U_SYS_DNXM\", \"U_SYS_VENC\", \"U_SYS_FOAL\", \"U_SYS_ORTR\", \"U_SYS_FOEX\") VALUES (\'{skComplet}\',\'{venta_sk}\', \'{sellerID}\', \'{caja}\', {sellerID}, \'{change}\', \'{partyIdentifier}\', \'\',\'\', \'0\',\'{description}\',\'0\',\'\',\'{fecha_process}\', \'0\', \'{fecha_process}\', \'{horastr}\', \'{horastr}\', \'{horastr}\', \'0\', \'0\', \'0\', \'{fp_amount}\', \'{partyCode}\', \'\', \'\', \'Y\', \'{docnumultimo}\', \'0\', \'\', \'0\', \'N\', \'N\', \'{sellerID}\', \'{sucursal}\', \'\', \'{fp_amount}\', \'X\', \'N\', \'{tpp}\', \'N\', \'N\', \'\', \'E\', \'{venta_sk_n}\')'
                            }
                        }
                print(data)
                # tabla @SYS_PDETALLEDEVOL
                data = {
                    "FilterEq": {
                        "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDETALLEDEVOL\"(\"Code\", \"Name\", \"U_SYS_ALMA\", \"U_SYS_CANT\", \"U_SYS_CENC\", \"U_SYS_CODA\", \"U_SYS_CODB\", \"U_SYS_CUEN\", \"U_SYS_DCTO\", \"U_SYS_DESC\", \"U_SYS_FECH\", \"U_SYS_FOLT\", \"U_SYS_IDCE\", \"U_SYS_IIMP\", \"U_SYS_IMCD\", \"U_SYS_IMPD\", \"U_SYS_IMPN\", \"U_SYS_IMPU\", \"U_SYS_MDCF\", \"U_SYS_NUME\", \"U_SYS_PBCD\", \"U_SYS_PBSD\", \"U_SYS_PDCF\", \"U_SYS_PNCD\", \"U_SYS_PNSD\", \"U_SYS_PAPU\", \"U_SYS_PROY\", \"U_SYS_PUNT\", \"U_SYS_SERV\", \"U_SYS_TDEI\", \"U_SYS_TMIN\", \"U_SYS_UNBA\") VALUES (\'{skComplet}\', \'{venta_sk}\',\'{sucursal}\', \'{quantity}\', \'\', \'{sku}\' , \'{barcode}\', \'\', \'0\', \'{description}\', \'{fecha_process}\', \'{venta_sk}\',\'0\',\'\',\'{total_disc}\', \'0\', \'\', \'{iva}\', \'0\', \'\', \'{priceWoVAT}\', \'{precio_brutoSD}\', \'0\',\'{subtotal}\', \'{iva}\', \'0\', \'\', \'0\', \'N\',\'{sellerID}\', \'IN\', \'N\')'
                            }
                    }
                print(data)
                # tabla @SYS_PPAGOTANS
                data = {
                        "FilterEq": {
                            "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PPAGOTANS\"(\"Code\", \"Name\", \"U_SYS_HOCA\", \"U_SYS_NUME\", \"U_SYS_NUMC\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_FOLT\", \"U_SYS_BANC\",\"U_SYS_NUMT\", \"U_SYS_AUTT\", \"U_SYS_VIGT\", \"U_SYS_FOPA\", \"U_SYS_REFE\", \"U_SYS_MONP\", \"U_SYS_MONN\",\"U_SYS_MONB\", \"U_SYS_CCTP\") VALUES (\'{skComplet}\', \'{venta_sk}\', \'{fecha_process}\', \'0\', \'0\', \'{fecha_process}\', \'{fecha_process}\', \'{skComplet}\', \'\', \'\', \'\', \'\', \'{fopa}\', \'\', \'{subtotal}\', \'{total_disc}\',\'{precio_brutoSD}\', \'\')'
                        }
                }
                print(data)
                
        else:
            print("Otra acción")

    #Query para la tabla PTRANSACCIONES 


    # response = api_hana(data)

    # Procesa la respuesta o maneja errores si es necesario
    # if isinstance(response, dict):
    #     return JsonResponse(response)
    # else:
    #     # La respuesta es un mensaje de error
    #     return JsonResponse({"error": response})

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
            
def api_hana(data):
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

def selectSucu():
    with connection.cursor() as cursor:
        cursor.execute("SELECT SUBSTRING(venta_sk, 8, 1) AS tipo_transaccion, sucursal, COUNT(*) AS repeticiones FROM consolidacion_bancarianueva.crud_transacctionpago GROUP BY SUBSTRING(venta_sk, 8, 1), sucursal")
        results = cursor.fetchall()

    return results 

def extractFolioSig(response):
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


# funciones para vistas principal
def inicio2(request):
    return render(request, "paginas/inicio.html")