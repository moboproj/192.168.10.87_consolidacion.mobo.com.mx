from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 
from django.views.decorators.csrf import csrf_exempt
from django.db import connection, transaction
from datetime import date, datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from pymysql import connect, cursors
from collections import OrderedDict
import requests
import pymysql
import psycopg2
import pyodbc
import traceback
import logging
import json
import re
db = pymysql.connect(host='40.124.171.87', user='jesanchez', password='moboweb5226', database='consolidacion', cursorclass=cursors.DictCursor )
cursor = db.cursor()
@csrf_exempt
def menu_MAIN(request):
    return render(request, 'MAIN/baseMain.html')

def dashboard(request):
      return render(request, 'MAIN/dashboard.html')
@csrf_exempt
def conectar_bd():
     try:
         db = pymysql.connect(
             host='40.124.171.87',
             user='jesanchez',
             password='moboweb5226',
             database='consolidacion',
             cursorclass=cursors.DictCursor
         )
         return db
     except Exception as e:
         logging.error("Error al conectar a la base de datos: %s", e)
         return None
     
def SumaExBan(request):
    try:
        with conectar_bd() as cursor:
            if cursor:
                try:
                    # Obtener la fecha más reciente
                    cursor.execute("SELECT MAX(Fecha_Op) AS Fecha_Reciente FROM consolidacion.QAExtracto;")
                    fecha_reciente_result = cursor.fetchone()
                    fecha_reciente = fecha_reciente_result['Fecha_Reciente']              
                    cursor.execute("SELECT Fecha_Op, NuCuenta, ROUND(SUM(Abono), 2) AS Total_dia FROM consolidacion.QAExtracto WHERE NuCuenta IN ('110543411', '110579440', '4045893245', '4067964031')GROUP BY Fecha_Op = %s, NuCuenta;", [fecha_reciente])

                    resultados = cursor.fetchall()
                    datos_procesados = []
                    for fila in resultados:
                        datos_procesados.append({
                            'Total_dia': float(fila['Total_dia']),
                            'NuCuenta': fila['NuCuenta'],
                            'Fecha_Op': fecha_reciente,
                        })

                    print("Datos procesados:", datos_procesados)
                    print("Fecha más reciente:", fecha_reciente)

                    return JsonResponse(datos_procesados, safe=False)                
                except Exception as e:
                    print("Error al extraer los datos en SumaHana:", e)
                    logging.error("Error al ejecutar la consulta: %s", e)
                    return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        print("Error en la vista SumaHANA:", e)
        logging.error("Error al conectar a la base de datos: %s", e)
        return JsonResponse({'error': str(e)})

def SumaHana(request):
     try:
        with conectar_bd() as cursor:
            if cursor:
                try:
                    # Obtener la fecha más reciente
                    cursor.execute("SELECT MAX(fecha_c) AS Fecha_Reciente FROM consolidacion.HANA;")
                    fecha_reciente_result = cursor.fetchone()
                    fecha_reciente = fecha_reciente_result['Fecha_Reciente']
                    cursor.execute("SELECT Fecha_Op, NuCuenta, ROUND(SUM(Abono), 2) AS Total_dia FROM consolidacion.QAExtracto WHERE NuCuenta IN ('110543411', '110579440', '4045893245', '4067964031')GROUP BY Fecha_Op = %s, NuCuenta;", [fecha_reciente])

                    resultados = cursor.fetchall()

                    datos_procesados = []
                    for fila in resultados:
                        datos_procesados.append({
                            'Total_dia': float(fila['Total_dia']),
                            'NuCuenta': fila['NuCuenta'],
                            'Fecha_Op': fecha_reciente,
                        })

                    print("Datos procesados:", datos_procesados)
                    print("Fecha más reciente:", fecha_reciente)

                    return JsonResponse(datos_procesados, safe=False)
                except Exception as e:
                    print("Error en la vista SumaHANA:", e)
                    logging.error("Error al ejecutar la consulta: %s", e)
                    return JsonResponse({'error': str(e)}, status=500)
     except Exception as e:
        print("Error en la vista SumaHANA:", e)
        logging.error("Error al conectar a la base de datos: %s", e)
        return JsonResponse({'error': str(e)})

def totalesxtienda(request):
     try:
          with conectar_bd() as cursor:
             if cursor:
                  try:
                       cursor.execute("select ROUND(SUM(totales), 2) AS totales, fecha_c, cuenta_base_bancos from hanaUnionS where cuenta_base_bancos in (3411,9440, 4031, 3245)  and fecha_c = '2024-01-02' group by fecha_c,cuenta_base_bancos;")
                       resultados = cursor.fetchall()
                       datos_procesados = []
                       for fila in resultados:
                            datos_procesados.append({
                                 'totales': float(fila['totales']),
                                 'fecha_c': str(fila['fecha_c']),
                                 'cuenta_base_bancos': fila['cuenta_base_bancos'],
                            })
                       print(datos_procesados)
                       return JsonResponse(datos_procesados, safe=False)
                  except Exception as e:
                       print("Error en la vista totalesxtienda", e)
                       logging.error("Error al ejecutar la consulta: %s", e)
                       return JsonResponse({'error': str(e)}, status=500)
     except Exception as e:
          print("Error en la vista hanaUnionS: ", e)
          logging.error("Error al conectar a la base de datos: %s", e)
          return JsonResponse({'Error': str(e)})

def vwTxT(request):
    try:
        connection = conectar_bd()
        if connection is None:
            raise Exception("No se pudo obtener una conexión a la base de datos")
        
        numero_tienda = request.GET.get('numero_tienda')
        
        with connection.cursor() as cursor:
            try:
                query = "SELECT * FROM Insertar_QA WHERE NuCuenta LIKE %s ORDER BY Fecha_Op DESC limit 500"
                cursor.execute(query, ['%' + numero_tienda + '%'])
                resultados = cursor.fetchall()
                return JsonResponse(resultados, safe=False)
            except Exception as e:
                logging.error("Error al ejecutar la consulta: %s", e)
                return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logging.error("Error en la vista de vwTxT: %s", e)
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        if connection:
            connection.close()

def nomach(request):
     try:
          with conectar_bd() as cursor:
            if cursor:
                 try:
                      cursor.execute("SELECT * FROM NOMACH")
                      resultados = cursor.fetchall()
                      datos_procesados = []
                      for fila in resultados:
                           datos_procesados.append({
                                'Fecha_Op': str(fila['Fecha_Op']),
                                'no_sucursal': fila['no_sucursal'],
                                'Abono': float(fila['Abono']) if fila['Abono'] is not None else None,
                                'fecha_ini_amex': str(fila['fecha_ini_amex']) if fila['fecha_ini_amex'] is not None else None,
                                'fecha_fin_amex': str(fila['fecha_fin_amex']) if fila['fecha_fin_amex'] is not None else None,
                                'sucursal': fila['sucursal'] if fila['sucursal'] is not None else None,
                                'pagado': float(fila['pagado']) if fila['pagado'] is not None else None,

                           })
                      print(datos_procesados)
                      return JsonResponse(datos_procesados, safe=False)
                 except Exception as e:
                      print("error en la vista de vwTxT", e)
                      logging.error("Error al ejecutar la consulta: %s", e)
                      return JsonResponse({'error': str(e)}, status=500)
     except Exception as e:
          print("Error en la vista de vwTxT", e)
          logging.error("Error al conectar con la base de datos: %s", e)
          return JsonResponse({'Error': str(e)})
      
@csrf_exempt
def CONSOLIDACIONTIPO(request):
    
    fecha_extrac = request.GET.get('fecextrac')
    FecextFin = request.GET.get('FecextFin')

    if not fecha_extrac:
        return JsonResponse({'error': 'No se proporcionó una fecha válida.'}, status=400)

    try:
        # Convertir la cadena de fecha original en un objeto datetime
        fecha_original = datetime.strptime(fecha_extrac, '%Y-%m-%d')
        # Restar un día para obtener la fecha reducida
        fecha_reducida = fecha_original - timedelta(days=1)
        # Convertir de nuevo a cadena en el mismo formato
        fecha_reducida_str = fecha_reducida.strftime('%Y-%m-%d')
        #--------------------------------------------------------------
        # Convertir la cadena de fecha original en un objeto datetime
        fecha_orfn = datetime.strptime(FecextFin, '%Y-%m-%d')
        # Restar un día para obtener la fecha reducida
        fecha_redfin = fecha_orfn - timedelta(days=1)
        # Convertir de nuevo a cadena en el mismo formato
        fecha_redfin_str = fecha_redfin.strftime('%Y-%m-%d')
        conexion = conectar_bd()
        if not conexion:
            return JsonResponse({'error': 'No se pudo establecer la conexión a la base de datos.'}, status=500)

        # Consulta con la fecha original
        with conexion.cursor() as cursor:
            query_original = "CALL Porsentaje_CB(%s, %s, 0, 1);"
            cursor.execute(query_original, [fecha_extrac,FecextFin])
            datos_original = cursor.fetchall()
            print(datos_original)
        # Consulta con la fecha reducida
        with conexion.cursor() as cursor:
            query_reducida = "CALL Porsentaje_CB(%s, %s, NULL, 3);"
            cursor.execute(query_reducida, [fecha_reducida_str, fecha_redfin_str])
            datos_reducida = cursor.fetchall()

        conexion.close()

        # Paginación para ambas consultas (opcional, si deseas paginar ambas)
        paginator_original = Paginator(datos_original, 100)
        page_original = request.GET.get('page_original')
        try:
            datos_paginados_original = paginator_original.page(page_original)
        except PageNotAnInteger:
            datos_paginados_original = paginator_original.page(1)
        except EmptyPage:
            datos_paginados_original = paginator_original.page(paginator_original.num_pages)

        paginator_reducida = Paginator(datos_reducida, 100)
        page_reducida = request.GET.get('page_reducida')
        try:
            datos_paginados_reducida = paginator_reducida.page(page_reducida)
        except PageNotAnInteger:
            datos_paginados_reducida = paginator_reducida.page(1)
        except EmptyPage:
            datos_paginados_reducida = paginator_reducida.page(paginator_reducida.num_pages)

        return JsonResponse({
            'datos_original': list(datos_paginados_original),
            'datos_reducida': list(datos_paginados_reducida)
        }, safe=False)

    except pyodbc.Error as e:
        print(f'Error al ejecutar la consulta: {str(e)}')
        return JsonResponse({'error': f'Error al ejecutar la consulta: {str(e)}'}, status=500)
    except Exception as e:
        print(f'Error inesperado: {str(e)}')
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)
    
@csrf_exempt
def CONSOLIDACIONEFECTIVO(request):
    
    fecha_extrac = request.GET.get('fecextrac')
    if not fecha_extrac:
        return JsonResponse({'error': 'No se proporcionó una fecha válida.'}, status=400)

    try:
        # Convertir la cadena de fecha original en un objeto datetime
        fecha_original = datetime.strptime(fecha_extrac, '%Y-%m-%d')
        # Restar un día para obtener la fecha reducida
        fecha_reducida = fecha_original - timedelta(days=1)
        # Convertir de nuevo a cadena en el mismo formato
        fecha_reducida_str = fecha_reducida.strftime('%Y-%m-%d')

        conexion = conectar_bd()
        if not conexion:
            return JsonResponse({'error': 'No se pudo establecer la conexión a la base de datos.'}, status=500)

        # Consulta con la fecha original
        with conexion.cursor() as cursor:
            query_original = "select NuCuenta, Fecha_Op, sum(Abono) as Abono  from EFEC_Bancos where Fecha_Op = %s group by NuCuenta,Fecha_Op"
            cursor.execute(query_original, [fecha_extrac])
            datos_original = cursor.fetchall()

        # Consulta con la fecha reducida
        with conexion.cursor() as cursor:
            query_reducida = "select round(sum(Total),2)as total, fecha, origen from efectivo_vista_dasboard where fecha = %s group by origen, fecha;"
            cursor.execute(query_reducida, [fecha_reducida_str])
            datos_reducida = cursor.fetchall()

        conexion.close()

        # Paginación para ambas consultas (opcional, si deseas paginar ambas)
        paginator_original = Paginator(datos_original, 100)
        page_original = request.GET.get('page_original')
        try:
            datos_paginados_original = paginator_original.page(page_original)
        except PageNotAnInteger:
            datos_paginados_original = paginator_original.page(1)
        except EmptyPage:
            datos_paginados_original = paginator_original.page(paginator_original.num_pages)

        paginator_reducida = Paginator(datos_reducida, 100)
        page_reducida = request.GET.get('page_reducida')
        try:
            datos_paginados_reducida = paginator_reducida.page(page_reducida)
        except PageNotAnInteger:
            datos_paginados_reducida = paginator_reducida.page(1)
        except EmptyPage:
            datos_paginados_reducida = paginator_reducida.page(paginator_reducida.num_pages)

        return JsonResponse({
            'datos_original': list(datos_paginados_original),
            'datos_reducida': list(datos_paginados_reducida)
        }, safe=False)

    except pyodbc.Error as e:
        print(f'Error al ejecutar la consulta: {str(e)}')
        return JsonResponse({'error': f'Error al ejecutar la consulta: {str(e)}'}, status=500)
    except Exception as e:
        print(f'Error inesperado: {str(e)}')
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)
    
def inicio(request):
    print ("ya")
    
def JoinAmex(request):
    
    try:
        with conectar_bd() as cursor:
            if cursor:
                cursor.execute("SELECT * FROM extAMEX ea JOIN fpAMEX fp ON fp.sucursal = ea.no_sucursal AND ea.Fecha_Op BETWEEN fp.fecha_ini_amex AND fp.fecha_fin_amex AND (fp.pagado = ea.Abono OR fp.pagado +1 = ea.Abono +1 OR fp.pagado -1 = ea.Abono-1)order by fp.fecha_ini_amex,fp.fecha_fin_amex,ea.no_sucursal;")
                resultados = cursor.fetchall()

                for r in resultados:
                     cursor.execute("INSERT INTO consolidacion (Fecha_Op, no_sucursal, Abono, fecha_ini_amex, fecha_fin_amex, sucursal, pagado, consolidado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                    (str(r['Fecha_Op']), r['no_sucursal'], float(r['Abono']), str(r['fecha_ini_amex']), str(r['fecha_fin_amex']), r['sucursal'], float(r['pagado']), 1))
                cursor.connection.commit()
                return JsonResponse(resultados, safe=False)
    except Exception as e:
        print(f"Error al ejecutar la consulta: {e}")
        return JsonResponse({'error': 'Hubo un problema al procesar la solicitud'}, status=500)
    
logger = logging.getLogger(__name__)

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
   

        if 'V' in str(venta_sk) or 'F' in str(venta_sk):
                data = {
                        "FilterEq" : {
                            "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PTRANSACCIONES\" (\"Code\", \"Name\", \"U_SYS_HOCA\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_SUCU\", \"U_SYS_CAJA\", \"U_SYS_CAJE\", \"U_SYS_CLMO\", \"U_SYS_SONE\", \"U_SYS_MEMB\", \"U_SYS_AGEV\", \"U_SYS_NUDS\", \"U_SYS_NUSI\", \"U_SYS_USAU\", \"U_SYS_IMPU\", \"U_SYS_SUBT\", \"U_SYS_TOTT\", \"U_SYS_TOTN\", \"U_SYS_CAMB\", \"U_SYS_SALA\", \"U_SYS_COME\", \"U_SYS_TRAS\", \"U_SYS_VPUG\", \"U_SYS_SERV\", \"U_SYS_FACT\", \"U_SYS_CANC\", \"U_SYS_LINE\", \"U_SYS_CANE\", \"U_SYS_DEES\", \"U_SYS_TIPO\", \"U_SYS_ESRE\", \"U_SYS_CLAP\", \"U_SYS_TEAP\", \"U_SYS_COMA\", \"U_SYS_ESAP\", \"U_SYS_FPRO\", \"U_SYS_HPRO\", \"U_SYS_LIPE\", \"U_SYS_VSPC\", \"U_SYS_DECU\", \"U_SYS_DESB\", \"U_SYS_ ESRS\", \"U_SYS_FACD\", \"U_SYS_FOCU\", \"U_SYS_FOVI\", \"U_SYS_IDCE\", \"U_SYS_IDEI\", \"U_SYS_IDEP\", \"U_SYS_IDPU\", \"U_SYS_OCUP\", \"U_SYS_ PDCF\", \"U_SYS_ POCU\", \"U_SYS_ PROY\", \"U_SYS_SELE\", \"U_SYS_TDEI\", \"U_SYS_TPRO\", \"U_SYS_VEVT\", \"U_SYS_TPSI\", \"U_SYS_MOSI\", \"U_SYS_MESI\", \"U_SYS_TISI\", \"U_SYS_PUNT\", \"U_SYS_MAPA\", \"U_SYS_ORTR\", \"U_SYS_FOEX\") VALUES  (\'{venta_sk}\',\'{venta_sk}\', \'{hora24h}\', \'{fecha_process}\', \'{horastr}\', \'{sucursal}\', \'{caja}\', \'{sellerID}\', \'{partyIdentifier}\', \'{codeSucursal}\', \'{partyCode}\', \'{sellerID}\', \'{venta_sk}\', \'0\', \'-1\', \'{iva}\', \'{subtotal}\', {total}, {fp_amount}, {change}, \'0\', \'\', \'N\', \'Y\', \'N\', \'N\', \'N\', \'N\', \'N\', \'N\', \'{venta_sk}\', \'N\', \'\', \'\', \'\', \'\', \'{fecha_process}\', \'{horastr}\', \'{priceListId}\', \'{venta_sk}\', \'0\', \'0\', \'N\', \'\', \'\', \'\', \'0\', \'0\', \'0\', \'0\', \'\', \'0\', \'0\', \'\', \'N\', \'0\', \'\', \'N\', \'X\', \'Y\', \'\', \'\', \'0\', \'N\',\'E\' \'{venta_sk_n}\')'
                        }
                    }
                print(data)
                # SYS_PDETALLETRANS
                data = {
                        "FilterEq": {
                            "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDETALLETRANS\" (\"Code\", \"Name\", \"U_SYS_FOLT\", \"U_SYS_CODA\", \"U_SYS_CODB\", \"U_SYS_CUEN\", \"U_SYS_ALMA\", \"U_SYS_CENC\", \"U_SYS_PROY\", \"U_SYS_DESC\", \"U_SYS_SERV\", \"U_SYS_NUME\", \"U_SYS_CANT\", \"U_SYS_CANA\", \"U_SYS_PNSD\", \"U_SYS_PNCD\", \"U_SYS_IMPN\", \"U_SYS_PBSD\", \"U_SYS_PBCD\", \"U_SYS_IMPU\", \"U_SYS_IMPD\", \"U_SYS_IMCD\", \"U_SYS_FECH\", \"U_SYS_FECE\", \"U_SYS_UNBA\", \"U_SYS_GARA\", \"U_SYS_CANC\", \"U_SYS_TMIN\", \"U_SYS_CNPA\", \"U_SYS_IIMP\", \"U_SYS_PROR\", \"U_SYS_PUNT\", \"U_SYS_POPU\", \"U_SYS_SERV\") VALUES (\'{venta_sk}\',\'{venta_sk}\', \'{venta_sk}\', \'{sku}\', \'{barcode}\', \'\', \'{sucursal}\', \'\', \'\', \'{description}\', \'\', \'\', \'{quantity}\', \'0\', \'{priceWoVAT}\', \'{pncd}\', \'IMPN\', \'{precio_brutoSD}\', \'{priceWoVAT}\', \'{iva}\', \'0\', \'{total_disc}\', \'{fecha_process}\', \'\', \'N\', \'N\',\'N\', \'IN\', \'0\', \'\', \'0\',\'0\',\'0\',\'N\')'
                        }
                    }
                print(data)
                # tabla de @SYS_PCOBROTRANS
                data = {
                        "FilterEq": {
                                "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PCOBROTRANS\"(\"Code\",\"Name\", \"U_SYS_HOCA\", \"U_SYS_NUME\", \"U_SYS_NUMC\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_FOLT\", \"U_SYS_BANC\", \"U_SYS_NUMT\", \"U_SYS_AUTT\", \"U_SYS_VIGT\", \"U_SYS_FOPA\", \"U_SYS_ANTI\", \"U_SYS_REFE\", \"U_SYS_MONP\", \"U_SYS_MONN\", \"U_SYS_MONB\", \"U_SYS_INRE\", \"U_SYS_CCTP\", \"U_SYS_TICA\", \"U_SYS_MONE\") VALUES (\'{venta_sk}\', \'{venta_sk}\', \'{hora24h}\',\'{sellerID}\',\'0\',\'{fecha_process}\',\'{horastr}\',\'{venta_sk}\',\'\',\'\',\'\',\'\',\'{fopa}\',\'\',\'\',\'{total}\', \'{total_disc}\', \'{precio_brutoSD}\',\'Y\', \'\',\'0\', \'0\')'
                            }
                    }
                print(data)
        elif 'D' in str(venta_sk) or 'N' in str(venta_sk):
                
                # tabla @SYS_PDEVOLUCIONES
                data = {
                    "FilterEq": {
                            "Qurey": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDEVOLUCIONES\" (\"Code\", \"Name\", \"U_SYS_AGEV\", \"U_SYS_CAJA\", \"U_SYS_CAJE\", \"U_SYS_CAMB\", \"U_SYS_CLMO\", \"U_SYS_COME\", \"U_SYS_CORE\", \"U_SYS_DESB\", \"U_SYS_DESC\", \"U_SYS_DIDE\", \"U_SYS_FACD\", \"U_SYS_FECH\", \"U_SYS_FOTR\", \"U_SYS_FPRO\", \"U_SYS_HOCA\", \"U_SYS_HORA\", \"U_SYS_HPRO\", \"U_SYS_IDCE\", \"U_SYS_IDEI\", \"U_SYS_IDPU\", \"U_SYS_IMPO\", \"U_SYS_MEMB\", \"U_SYS_MESI\", \"U_SYS_MODE\", \"U_SYS_MOSI\", \"U_SYS_NUDS\", \"U_SYS_PDCF\", \"U_SYS_PROY\", \"U_SYS_PUDE\", \"U_SYS_SELE\", \"U_SYS_SERV\", \"U_SYS_SONE\", \"U_SYS_SUCU\", \"U_SYS_TISI\", \"U_SYS_TOTN\", \"U_SYS_TPSI\", \"U_SYS_TRAS\", \"U_SYS_VSPC\", \"U_SYS_DNXM\", \"U_SYS_VENC\", \"U_SYS_FOAL\", \"U_SYS_ORTR\", \"U_SYS_FOEX\") VALUES (\'{venta_sk}\',\'{venta_sk}\', \'{sellerID}\', \'{caja}\', {sellerID}, \'{change}\', \'{partyIdentifier}\', \'\',\'\', \'0\',\'{description}\',\'0\',\'\',\'{fecha_process}\', \'0\', \'{fecha_process}\', \'{horastr}\', \'{horastr}\', \'{horastr}\', \'0\', \'0\', \'0\', \'{fp_amount}\', \'{partyCode}\', \'\', \'\', \'Y\', \'{venta_sk}\', \'0\', \'\', \'0\', \'N\', \'N\', \'{sellerID}\', \'{sucursal}\', \'\', \'{fp_amount}\', \'X\', \'N\', \'{venta_sk}\', \'N\', \'N\', \'\', \'E\', \'{venta_sk_n}\')'
                            }
                        }
                print(data)
                # tabla @SYS_PDETALLEDEVOL
                data = {
                    "FilterEq": {
                        "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PDETALLEDEVOL\"(\"Code\", \"Name\", \"U_SYS_ALMA\", \"U_SYS_CANT\", \"U_SYS_CENC\", \"U_SYS_CODA\", \"U_SYS_CODB\", \"U_SYS_CUEN\", \"U_SYS_DCTO\", \"U_SYS_DESC\", \"U_SYS_FECH\", \"U_SYS_FOLT\", \"U_SYS_IDCE\", \"U_SYS_IIMP\", \"U_SYS_IMCD\", \"U_SYS_IMPD\", \"U_SYS_IMPN\", \"U_SYS_IMPU\", \"U_SYS_MDCF\", \"U_SYS_NUME\", \"U_SYS_PBCD\", \"U_SYS_PBSD\", \"U_SYS_PDCF\", \"U_SYS_PNCD\", \"U_SYS_PNSD\", \"U_SYS_PAPU\", \"U_SYS_PROY\", \"U_SYS_PUNT\", \"U_SYS_SERV\", \"U_SYS_TDEI\", \"U_SYS_TMIN\", \"U_SYS_UNBA\") VALUES (\'{venta_sk}\', \'{venta_sk}\',\'{sucursal}\', \'{quantity}\', \'\', \'{sku}\' , \'{barcode}\', \'\', \'0\', \'{description}\', \'{fecha_process}\', \'{venta_sk}\',\'0\',\'\',\'{total_disc}\', \'0\', \'\', \'{iva}\', \'0\', \'\', \'{priceWoVAT}\', \'{precio_brutoSD}\', \'0\',\'{subtotal}\', \'{iva}\', \'0\', \'\', \'0\', \'N\',\'{sellerID}\', \'IN\', \'N\')'
                            }
                    }
                print(data)
                # tabla @SYS_PPAGOTANS
                data = {
                        "FilterEq": {
                            "Query": f'INSERT INTO \"MOBO_QA\".\"@SYS_PPAGOTANS\"(\"Code\", \"Name\", \"U_SYS_HOCA\", \"U_SYS_NUME\", \"U_SYS_NUMC\", \"U_SYS_FECH\", \"U_SYS_HORA\", \"U_SYS_FOLT\", \"U_SYS_BANC\",\"U_SYS_NUMT\", \"U_SYS_AUTT\", \"U_SYS_VIGT\", \"U_SYS_FOPA\", \"U_SYS_REFE\", \"U_SYS_MONP\", \"U_SYS_MONN\",\"U_SYS_MONB\", \"U_SYS_CCTP\") VALUES (\'{venta_sk}\', \'{venta_sk}\', \'{fecha_process}\', \'0\', \'0\', \'{fecha_process}\', \'{fecha_process}\', \'{venta_sk}\', \'\', \'\', \'\', \'\', \'{fopa}\', \'\', \'{subtotal}\', \'{total_disc}\',\'{precio_brutoSD}\', \'\')'
                        }
                }
                print(data)
                
        else:
            print("Otra acción")
            
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
    return results  

# seccion vistas en HOME 
def dashboard(request):
      return render(request, 'MAIN/dashboard.html')

def Edashboard(request):
     return render(request, 'MAIN/Efec_dashboard.html')

def tablero(request):
    
     return render(request, 'MAIN/tablero.html')

# funcion para consultas de nuevo tablero lineal ---> REVISAR
def graflineal(request):
     with connection.cursor() as cursor:
          cursor.execute("")
          extractos = cursor.fetchall()

          cursor.execute("")
          ventas = cursor.fetchall()
    
     data_extractos = procesar_datos_extractos(extractos)
     data_ventas = procesar_datos_ventas(ventas)

     context = {
          'dataExtractos': data_extractos,
          'dataVentas': data_ventas
     }
     return render(request, 'tablero.html', context)

def procesar_datos_extractos(extractos):
     data_extractos = {
          'bbva' : [extracto[1] for extracto in extractos],
          'amex': [extracto[2] for extracto in extractos],
          'hsbc': [extracto[3] for extracto in extractos],
     }
     return data_extractos

def procesar_datos_ventas(ventas):
     data_ventas = [venta[1] for venta in ventas]
     return data_ventas

@csrf_exempt
def vistaTotalxTienda(request):
    return render(request, 'MAIN/TotalxTienda.html')

@csrf_exempt
def dataFiltro(request):
    try:
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin =  request.GET.get('fecha_fin')
        no_sucursal = request.GET.get('no_sucursal')

        conexion = conectar_bd()
        if conexion:
            with conexion.cursor() as cursor:
                query = 'SELECT * FROM CB_TotalxTiendas WHERE 1=1'
                params = []

                if fecha_inicio and fecha_fin:
                    query += " AND Fecha_Op BETWEEN %s AND %s"
                    params.append(fecha_inicio)
                    params.append(fecha_fin)
                
                if no_sucursal:
                    query += " AND no_sucursal = %s"
                    params.append(no_sucursal)
                
                cursor.execute(query, params)
                registros = cursor.fetchall()

                data = []
                grouped_data = {}
                for registro in registros:
                    registro_json = [
                        registro['no_sucursal'],
                        registro['sucursal'],
                        registro['Total_ex'],
                        registro['MPT'],
                        registro['NuCuenta'],
                        registro['Fecha_Op'],
                        registro['Ref_ampl'],
                        registro['Banco'],
                        registro['afiliacion_bbva'],
                        registro['fv_afiliacion_']
                    ]
                    no_sucursal = registro['no_sucursal']
                    if no_sucursal not in grouped_data:
                        grouped_data[no_sucursal] = []
                    grouped_data[no_sucursal].append(registro_json)
                for no_sucursal, registro in grouped_data.items():
                    data.append(registro[0])
                    print("agrupado", grouped_data)
                return JsonResponse({'data': data, 'grouped_data': grouped_data})
        else:
            return JsonResponse({'error': 'No se puede establecer la conexion a la base de datos.'}, status=500)
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Error: {error_message}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def Tabla_detalle(request):
    return render(request, 'MAIN/Tabla_CB.html')

@csrf_exempt
def ventas_detalles_v2(request):
    try:
        no_sucursal = request.GET.get('no_sucursal')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipoTransaccion = request.GET.get('tipo_transaccion')

        if(tipoTransaccion == 'Tarjeta'):
            if not fecha_inicio:
                raise ValueError("Fecha de inicio es requerida")

            fecha = datetime.strptime(fecha_inicio, '%Y-%m-%d') - timedelta(days=1)
            fecha = fecha.strftime('%Y-%m-%d')
            
            fecha2 = datetime.strptime(fecha_fin, '%Y-%m-%d') - timedelta(days=1)
            fecha2 = fecha2.strftime('%Y-%m-%d')
            

            print(f"Valor de no_sucursal recibido: {no_sucursal}")
            print(f"Valor de fecha_inicio recibido: {fecha_inicio}")
            print(f"Valor de fecha_fin recibido: {fecha_fin}")

            conexion = conectar_bd()
            if conexion:
                with conexion.cursor() as cursor:
                    query_ventas = "SELECT * FROM Ventas_modal WHERE fecha BETWEEN %s AND %s AND sucursal = %s order by fecha asc"
                    cursor.execute(query_ventas, [fecha, fecha2, no_sucursal])
                    registro_ventas = cursor.fetchall()
                    data_ventas = []
                    for registro in registro_ventas:
                        registro_json = {
                            'idtbl_ExtractosBancarios': registro['idtbl_ExtractosBancarios'],
                            'folio_venta': registro['folio_venta'],
                            'monto_pagado': registro['monto_pagado'],
                            'forma_pago_id': registro['forma_pago_id'],
                            'sucursal': registro['sucursal'],
                            'fecha': registro['fecha'].isoformat(),
                            'Origen': registro['Origen']
                        }
                        data_ventas.append(registro_json)
                    
                    query_detalle = "SELECT * FROM Union_Extractos WHERE Fecha_Op BETWEEN %s AND %s AND no_sucursal = %s ORDER BY CAST(no_sucursal AS UNSIGNED),Fecha_Op ASC"
                    cursor.execute(query_detalle, [fecha_inicio, fecha_fin, no_sucursal])
                    registro_detalle = cursor.fetchall()
                    data_detalle = []
                    for registro in registro_detalle:
                        registro_json = {
                            'NuCuenta': registro['NuCuenta'],
                            'idtbl_ExtractosBancarios': registro['idtbl_ExtractosBancarios'],
                            'no_sucursal': registro['no_sucursal'],
                            'Abono': registro['Abono'],
                            'Fecha_Op': registro['Fecha_Op'].isoformat(),
                        }   
                        data_detalle.append(registro_json)
                    print(f"Data Detalle tarjetas: {data_detalle}")
                    return JsonResponse({'data_ventas': data_ventas, 'data_detalle': data_detalle})
            else:
                return JsonResponse({'error': 'No se puede establecer la conexion a la base de datos.'}, status=500)
        else:
            print("Entro al else de efectivo")
            if not fecha_inicio:
                raise ValueError("Fecha de inicio es requerida")

            fecha = datetime.strptime(fecha_inicio, '%Y-%m-%d') - timedelta(days=1)
            fecha = fecha.strftime('%Y-%m-%d')
            
            fecha2 = datetime.strptime(fecha_fin, '%Y-%m-%d') - timedelta(days=1)
            fecha2 = fecha2.strftime('%Y-%m-%d')
            

            print(f"Valor de no_sucursal recibido: {no_sucursal}")
            print(f"Valor de fecha_inicio recibido: {fecha}")
            print(f"Valor de fecha_fin recibido: {fecha2}")

            conexion = conectar_bd()
            if conexion:
                with conexion.cursor() as cursor:
                    query_ventas = "SELECT * FROM vistaCUATRO_Efectivo WHERE fecha BETWEEN %s AND %s AND sucursal = %s order by fecha asc"
                    print (query_ventas)

                    cursor.execute(query_ventas, [fecha, fecha2, no_sucursal])
                    
                    registro_ventas = cursor.fetchall()
                    #print(registro_ventas)
                    data_ventas = []
                    for registro in registro_ventas:
                        registro_json = {
                            'idtbl_ExtractosBancarios': registro['id_posone'],
                            'folio_venta': registro['folio_venta'],
                            'monto_pagado': registro['ventas'],
                            'forma_pago_id': registro['CB'],
                            'sucursal': registro['sucursal'],
                            'fecha': registro['fecha'].isoformat(),
                            'Origen': registro['origen']
                        }
                        data_ventas.append(registro_json)
                       # print("Registro jason",registro_json)
                    print(no_sucursal)
                    # query_detalle = "SELECT * FROM Union_Extractos WHERE Fecha_Op BETWEEN %s AND %s AND no_sucursal = %s ORDER BY CAST(no_sucursal AS UNSIGNED),Fecha_Op ASC"
                    query_detalle = "SELECT * FROM vistaCINCO_Efectivo WHERE Fecha_Op BETWEEN %s AND %s AND sucursal = %s ORDER BY CAST(sucursal AS UNSIGNED),Fecha_Op ASC"
                    cursor.execute(query_detalle, [fecha_inicio, fecha_fin, no_sucursal])
                    print(no_sucursal)
                    registro_detalle = cursor.fetchall()
                    data_detalle = []
                    for registro in registro_detalle:
                        registro_json = {
                            'NuCuenta': registro['numero_cuenta'],
                            'idtbl_ExtractosBancarios': registro['idtbl_ExtractosBancarios'],
                            'no_sucursal': registro['sucursal'],
                            'Abono': registro['abono'],
                            'Fecha_Op': registro['Fecha_Op'].isoformat(),
                        }   
                        data_detalle.append(registro_json)
                    print(f"Data Detalle: {data_detalle}")
                    return JsonResponse({'data_ventas': data_ventas, 'data_detalle': data_detalle})
            else:
                return JsonResponse({'error': 'No se puede establecer la conexion a la base de datos.'}, status=500)
        
        
    except Exception as e:
        error_mensaje = traceback.format_exc()
        print(f"Error: {error_mensaje}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def modal_detalle(request):
    try:
        no_sucursal = request.GET.get('no_sucursal')
        
        
        fecha_venta = request.GET.get('fecha_venta')
        fecha_venta_fin = request.GET.get('fecha_venta_fin')
        
        fecha_extrac = request.GET.get('fecha_extrac')
        fecha_extrac_fin = request.GET.get('fecha_extrac_fin')
        
        tipoTransaccion = request.GET.get('tipo_transaccion')
        
        if(tipoTransaccion == 'Tarjeta'):
            # Validar que no_sucursal esté presente y sea válido
            if not no_sucursal:
                raise ValueError("No se proporcionó el número de sucursal.")

            # Validar que exactamente una de las fechas esté presente
            if fecha_venta and fecha_extrac:
                raise ValueError("Solo se puede proporcionar una fecha a la vez (fecha_venta o fecha_extrac).")

            # Validar que al menos una fecha esté presente
            if not fecha_venta and not fecha_extrac:
                raise ValueError("Se requiere al menos una fecha (fecha_venta o fecha_extrac).")

            conexion = conectar_bd()
            if conexion:
                with conexion.cursor() as cursor:
                    if fecha_venta:
                        query_modal_ventas = "SELECT * FROM Ventas_modal WHERE sucursal = %s AND fecha BETWEEN %s AND %s  order by fecha asc"
                        cursor.execute(query_modal_ventas, [no_sucursal, fecha_venta,fecha_venta_fin ])
                        registros_vm = cursor.fetchall()
                        data_modal_venta = []
                        for registro in registros_vm:
                            registro_json = {
                                'idtbl_ExtractosBancarios': registro['idtbl_ExtractosBancarios'],
                                'folio_venta': registro['folio_venta'],
                                'monto_pagado': registro['monto_pagado'],
                                'forma_pago_id': registro['forma_pago_id'],
                                'sucursal': registro['sucursal'],
                                'fecha': registro['fecha'].isoformat(),
                                'Origen': registro['Origen']
                            }
                            data_modal_venta.append(registro_json)
                        print("ventas", data_modal_venta)
                        return JsonResponse({'data_ventas': data_modal_venta})
                    
                    elif fecha_extrac:
                        # Consulta para fecha_extrac
                        query_modal_extr = "SELECT * FROM Union_Extractos WHERE no_sucursal = %s AND Fecha_Op BETWEEN %s AND %s order by Fecha_Op asc;"
                        cursor.execute(query_modal_extr, [no_sucursal, fecha_extrac, fecha_extrac_fin])
                        registros_extrac = cursor.fetchall()
                        print("Resultados de la consulta para fecha_extrac:", registros_extrac)
                        data_extrac = []
                        for registro in registros_extrac:
                            registro_json = {
                                'NuCuenta': registro['NuCuenta'],
                                'idtbl_ExtractosBancarios': registro['idtbl_ExtractosBancarios'],
                                'no_sucursal': registro['no_sucursal'],
                                'Abono': registro['Abono'],
                                'Fecha_Op': registro['Fecha_Op'].isoformat(),
                                
                            }
                            data_extrac.append(registro_json)
                        print("extracto", registro_json)
                        return JsonResponse({'data_extracto': data_extrac})
            else:
                return JsonResponse({'error': 'No se puede establecer la conexión a la base de datos.'}, status=500)
        else:
            # Validar que no_sucursal esté presente y sea válido
            if not no_sucursal:
                raise ValueError("No se proporcionó el número de sucursal.")

            # Validar que exactamente una de las fechas esté presente
            if fecha_venta and fecha_extrac:
                raise ValueError("Solo se puede proporcionar una fecha a la vez (fecha_venta o fecha_extrac).")

            # Validar que al menos una fecha esté presente
            if not fecha_venta and not fecha_extrac:
                raise ValueError("Se requiere al menos una fecha (fecha_venta o fecha_extrac).")

            conexion = conectar_bd()
            if conexion:
                with conexion.cursor() as cursor:
                    if fecha_venta:
                        print("Entro a lo que se ncesita")
                        query_modal_ventas ="SELECT* FROM vistaCUATRO_Efectivo WHERE sucursal = %s AND fecha BETWEEN %s AND %s ORDER BY fecha ASC"
                        cursor.execute(query_modal_ventas, [no_sucursal, fecha_venta,fecha_venta_fin ])
                        registros_vm = cursor.fetchall()
                        data_modal_venta = []
                        for registro in registros_vm:
                            registro_json = {
                                'idtbl_ExtractosBancarios': registro['id_posone'],
                                'folio_venta': registro['folio_venta'],
                                'monto_pagado': registro['ventas'],
                                'forma_pago_id': registro['tipoTransaccion'],
                                'sucursal': registro['sucursal'],
                                'fecha': registro['fecha'].isoformat(),
                                'Origen': registro['origen']
                            }
                            data_modal_venta.append(registro_json)
                        print("ventas", data_modal_venta)
                        return JsonResponse({'data_ventas': data_modal_venta})
                    
                    elif fecha_extrac:
                        # Consulta para fecha_extrac
                        query_modal_extr = "SELECT * FROM vistaCINCO_Efectivo WHERE sucursal = %s AND Fecha_Op BETWEEN %s AND %s ORDER BY Fecha_Op ASC"
                        cursor.execute(query_modal_extr, [no_sucursal, fecha_extrac, fecha_extrac_fin])
                        registros_extrac = cursor.fetchall()
                        print("Resultados de la consulta para fecha_extrac:", registros_extrac)
                        data_extrac = []
                        for registro in registros_extrac:
                            registro_json = {
                                'NuCuenta': registro['numero_cuenta'],
                                'idtbl_ExtractosBancarios': registro['idtbl_ExtractosBancarios'],
                                'no_sucursal': registro['sucursal'],
                                'Abono': registro['abono'],
                                'Fecha_Op': registro['Fecha_Op'].isoformat(),
                                
                            }
                            data_extrac.append(registro_json)
                        print("extracto", registro_json)
                        return JsonResponse({'data_extracto': data_extrac})
            else:
                return JsonResponse({'error': 'No se puede establecer la conexión a la base de datos.'}, status=500)
    
    except ValueError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    
    except Exception as e:
        error_mensaje = traceback.format_exc()
        print(f"Error: {error_mensaje}")
        return JsonResponse({'error': str(e)}, status=500)

# pintar dos universos de ventas y extractos
def modal_detalle_V2(request):
    
    try:
        no_sucursal = request.GET.get('no_sucursal')
        fecha_venta = request.GET.get('fecha_venta')
        fecha_venta_fin = request.GET.get('fecha_venta_fin')
        fecha_extrac = request.GET.get('fecha_extrac')
        fecha_extrac_fin = request.GET.get('fecha_extrac_fin')
        consolidado = request.GET.get('consolidado')

        if not no_sucursal:
            raise ValueError("No se proporcionó la sucursal")
        if fecha_venta and fecha_extrac:
            raise ValueError("Se requiere al menos una fecha (fecha_venta o fecha_extrac)")

        conexion = conectar_bd()
        if conexion:
            with conexion.cursor() as cursor:
                query = """
                        SELECT *
                        FROM M_sales_vs_ext
                        WHERE (no_sucursal = %s OR %s IS NULL)
                        AND (Fecha BETWEEN %s AND %s OR %s IS NULL OR %s IS NULL)
                        AND (Fecha_Op BETWEEN %s AND %s OR %s IS NULL OR %s IS NULL)
                        """
                if consolidado == 'check':
                    query += "AND e1_idtbl_ExtractosBancarios IS NOT NULL"
                elif consolidado == 'times':
                    query += "AND e1_idtbl_ExtractosBancarios IS NULL"
                
                params = [no_sucursal, no_sucursal, fecha_venta, fecha_venta_fin, fecha_venta, fecha_venta_fin, fecha_extrac, fecha_extrac_fin, fecha_extrac, fecha_extrac_fin]
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return JsonResponse({'data': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)              
@csrf_exempt
class DataFetcher:
    def __init__(self, conexion):
        self.conexion = conexion

    def fetch_data(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None, sucursal=None):
        query = f"SELECT * FROM {table_name} WHERE Fecha_Op BETWEEN %s AND %s ORDER BY CAST(no_sucursal AS UNSIGNED) ASC "
        params = [fecha_inicio, fecha_fin]

        if no_sucursal:
            query += " AND no_sucursal = %s ORDER BY CAST(no_sucursal AS UNSIGNED) ASC"
            params.append(no_sucursal)

        if sucursal:
            query += " OR suc = %s ORDER BY CAST(no_sucursal AS UNSIGNED) ASC"
            params.append(sucursal)

        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    
    def fetch_data2(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        query = f"SELECT * FROM {table_name} WHERE fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}' ORDER BY sucursal, fecha ASC"
        params = [fecha_inicio, fecha_fin]

        if no_sucursal:
            query += " AND sucursal = '"+no_sucursal+"' ORDER BY sucursal, fecha ASC"
            params.append(no_sucursal)

        # Formatear la consulta con los parámetros incrustados


        with self.conexion.cursor() as cursor:
            cursor.execute(query)
            print(query)
            results = cursor.fetchall()
            print("Results from fetch_data2:", results)

        return results

    def fech_data4(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        query = f"SELECT * FROM {table_name} WHERE Fecha_Op BETWEEN %s AND %s "
        params = [fecha_inicio, fecha_fin]

        if no_sucursal:
            query += " AND no_sucursal = %s"
            params.append(no_sucursal)
        
        query += " ORDER BY CAST(no_sucursal AS UNSIGNED), Fecha_Op ASC"

        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        
    def dataSumExtractosEf(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        query = f"SELECT* FROM {table_name} VF WHERE VF.fecha BETWEEN %s AND %s"
        params = [fecha_inicio, fecha_fin]
        if no_sucursal:
            query += " AND VF.NOMBRE_SUCURSAL = %s"
            params.append(no_sucursal)
        query += " ORDER BY CAST(VF.NOMBRE_SUCURSAL AS UNSIGNED), VF.fecha ASC"
        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        
    def dataExtractoDetalle(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        query = f"SELECT* FROM {table_name} WHERE Fecha_Op BETWEEN %s AND %s"
        params = [fecha_inicio, fecha_fin] 
        if no_sucursal:
            query += " AND sucursal = %s"
            params.append(no_sucursal)
        query += " ORDER BY CAST(sucursal AS UNSIGNED), Fecha_Op ASC"
        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    def dataDetalleOrigen(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        query = f"SELECT* FROM {table_name} WHERE Fecha_Op BETWEEN %s AND %s"
        params = [fecha_inicio, fecha_fin] 
        if no_sucursal:
            query += " AND sucursal = %s"
            params.append(no_sucursal)
        query += " ORDER BY CAST(sucursal AS UNSIGNED), Fecha_Op ASC"
        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    def dataVentaDetalle(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        query = f"SELECT* FROM {table_name} WHERE fecha BETWEEN %s AND %s"
        params = [fecha_inicio, fecha_fin] 
        if no_sucursal:
            query += " AND sucursal = %s"
            params.append(no_sucursal)
        query += " ORDER BY CAST(sucursal AS UNSIGNED), fecha ASC"
        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    def dataVentaExtracto(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        query = f"SELECT* FROM {table_name} WHERE Fecha_Op BETWEEN %s AND %s"
        params = [fecha_inicio, fecha_fin] 
        if no_sucursal:
            query += " AND sucursal = %s"
            params.append(no_sucursal)
        query += " ORDER BY CAST(sucursal AS UNSIGNED), Fecha_Op ASC"
        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

        
    def fech_data5(self, table_name, fecha_inicio, fecha_fin, no_sucursal=None):
        # Convertir fecha_inicio a objeto datetime y restarle un día
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')  # Asumiendo que la fecha está en formato 'YYYY-MM-DD'
        fecha_inicio_dt -= timedelta(days=1)
        fecha_inicio = fecha_inicio_dt.strftime('%Y-%m-%d')  # Convertir de nuevo a string
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')  # Asumiendo que la fecha está en formato 'YYYY-MM-DD'
        fecha_fin_dt -= timedelta(days=1)
        
        fecha_fin = fecha_fin_dt.strftime('%Y-%m-%d')  # Convertir de nuevo a string

        query = f"CALL {table_name}(%s, %s"
        params = [fecha_inicio, fecha_fin]

        if no_sucursal and no_sucursal.isdigit():
            query += ", %s"
            params.append(no_sucursal)
        else:
            query += ", NULL"
        
        query += ", 2);"

        with self.conexion.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

@csrf_exempt
def filtrar_claves(registro, claves_excluir, orden_claves):
    filtered_registro = {k: v for k, v in registro.items() if k not in claves_excluir}
    ordered_registro = OrderedDict()
    for clave in orden_claves:
        if clave in filtered_registro:
            ordered_registro[clave] = filtered_registro[clave]
    return ordered_registro

@csrf_exempt
def TableDiccionario(request):
    try:
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        no_sucursal = request.GET.get('no_sucursal')
        sucursal = request.GET.get('sucursal')

        conexion = conectar_bd()
        if conexion:
            fetcher = DataFetcher(conexion)

            bbva_data = fetcher.fetch_data('V_BBVA3411', fecha_inicio, fecha_fin, no_sucursal, sucursal)
            hsbc_data = fetcher.fetch_data('V_HSBC3245', fecha_inicio, fecha_fin, no_sucursal, sucursal)
            hsbc_data2 = fetcher.fetch_data('V_HSBC2_4166', fecha_inicio, fecha_fin, no_sucursal, sucursal)
            amex_data = fetcher.fetch_data('V_AMEX', fecha_inicio, fecha_fin, no_sucursal, sucursal)
            fventas_data = fetcher.fetch_data2('Fventas', fecha_inicio, fecha_fin, no_sucursal)


            data_dict = {}

            def update_data_dict(data_list, key_column, value_column, total_column_name):
                for registro in data_list:
                    key = registro[key_column]
                    if key not in data_dict:
                        data_dict[key] = {
                            'no_sucursal': registro.get('no_sucursal', key),
                            'sucursal': registro.get('sucursal', 'N/A'),
                            'Total_ex': 0.0,
                            'Total_hsbc': 0.0,
                            'Total_hsbc2': 0.0,
                            'Total_amex': 0.0,
                            'MPT': 0.0,
                            'details': {
                                'Total_ex': [],
                                'Total_hsbc': [],
                                'Total_hsbc2': [],
                                'Total_amex': [],
                                'MPT': []
                            }
                        }
                    try:
                        if value_column in registro:
                            value = float(registro[value_column])
                            data_dict[key][total_column_name] += round(value, 2)
                            data_dict[key]['details'][total_column_name].append(registro)
                        else:
                            print(f"Warning: Column '{value_column}' not found in registro: {registro}")
                    except (ValueError, TypeError):
                        print(f"Warning: Could not convert {registro[value_column]} to float for key {key}")

            update_data_dict(bbva_data, 'no_sucursal', 'Total_ex', 'Total_ex')
            update_data_dict(hsbc_data, 'no_sucursal', 'Total_ex', 'Total_hsbc')
            update_data_dict(hsbc_data2, 'no_sucursal', 'Total_ex', 'Total_hsbc2')
            update_data_dict(amex_data, 'no_sucursal', 'Total_ex', 'Total_amex')

            for registro in fventas_data:
                key = registro['sucursal_']
                if key not in data_dict:
                    data_dict[key] = {
                        'no_sucursal': registro.get('no_sucursal', 'N/A'),
                        'sucursal': 'N/A',
                        'Total_ex': 0.0,
                        'Total_hsbc': 0.0,
                        'Total_hsbc2': 0.0,
                        'Total_amex': 0.0,
                        'MPT': 0.0,
                        'details': {
                            'Total_ex': [],
                            'Total_hsbc': [],
                            'Total_hsbc2': [],
                            'Total_amex': [],
                            'MPT': []
                        }
                    }
                try:
                    value = float(registro['MPT'])
                    data_dict[key]['MPT'] += round(value, 2)
                    data_dict[key]['details']['MPT'].append({
                        'MPT': registro.get('MPT'),
                        'afiliacion_bbva': registro.get('afiliacion_bbva'),
                        'afiliacion_hsbc': registro.get('afiliacion_hsbc'),
                        'afiliacion_amex': registro.get('afiliacion_amex'),
                        'fecha_ini': registro.get('fecha_ini'),
                        'fecha_fin': registro.get('fecha_fin'),
                    })
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert {registro['MPT']} to float for key {key}")

            claves_excluir = ['no_sucursal', 'Tipo_trans', 'Ref_ampl', 'No_Cl', 'afiliacion_bbva', 'afiliacion_hsbc', 'afiliacion_amex']
            orden_claves = {
                'Total_ex': ['Fecha_Op', 'Total_ex', 'NuCuenta', 'Tipo_trans', 'Ref_ampl', 'No_Cl', 'afiliacion_bbva'],
                'Total_hsbc': ['Fecha_Op', 'Total_ex', 'NuCuenta', 'Tipo_trans', 'Ref_ampl', 'No_Cl', 'afiliacion_hsbc'],
                'Total_hsbc2': ['Fecha_Op', 'Total_ex', 'NuCuenta', 'Tipo_trans', 'Ref_ampl', 'No_Cl', 'afiliacion_bbva'],
                'Total_amex': ['Fecha_Op', 'Total_ex', 'NuCuenta', 'Tipo_trans', 'Ref_ampl', 'No_Cl', 'afiliacion_amex'],
                'MPT': ['MPT','fecha_ini', 'fecha_fin','afiliacion_bbva', 'afiliacion_hsbc', 'afiliacion_amex']
            }

            combined_data = []
            for key, value in data_dict.items():
                total_consolidado = round(value['Total_ex'] + value['Total_hsbc'] + value['Total_hsbc2'] + value['Total_amex'] + value['MPT'], 2)
                value['Total_consolidado'] = "{:,.2f}".format(total_consolidado)

                filtered_details = {}
                for detail_key, detail_list in value['details'].items():
                    filtered_details[detail_key] = [filtrar_claves(registro, claves_excluir, orden_claves[detail_key]) for registro in detail_list]

                ordered_value = OrderedDict([
                    ('no_sucursal', value['no_sucursal']),
                    ('sucursal', value['sucursal']),
                    ('Total_ex', value['Total_ex']),
                    ('Total_hsbc', value['Total_hsbc']),
                    ('Total_hsbc2', value['Total_hsbc2']),
                    ('Total_amex', value['Total_amex']),
                    ('MPT', value['MPT']),
                    ('Total_consolidado', value['Total_consolidado']),
                    ('details', filtered_details),
                    
                ])
                combined_data.append(ordered_value)

            return JsonResponse({'data': combined_data})
        else:
            return JsonResponse({'error': 'No se puede establecer la conexión a la base de datos.'}, status=500)
    except Exception as e:
        import traceback
        error_message = traceback.format_exc()
        print(f"Error: {error_message}")
        return JsonResponse({'error': str(e)}, status=500)

def Diccionario_transacciones(request):
    try:
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        no_sucursal = request.GET.get('no_sucursal')
        tipoConsolidacion = request.GET.get('tipoConsolidacion')
        

        # print("fecha_inicio:", fecha_inicio)
        # print("fecha_fin:", fecha_fin)
        # print("no_sucursal:", no_sucursal)
        # print(tipoConsolidacion)
        # return tipoConsolidacion
        
        if (tipoConsolidacion == "Tarjetas"):

            conexion = conectar_bd()
            if conexion:
                fetcher = DataFetcher(conexion)

                # Obtener datos de las consultas
                data_bbva = fetcher.fech_data4('Union_Extractos', fecha_inicio, fecha_fin, no_sucursal)
                fventas_data = fetcher.fetch_data2('Punto_Venta', fecha_inicio, fecha_fin, no_sucursal)
                dataprose = fetcher.fech_data5('Porsentaje_CB', fecha_inicio, fecha_fin, no_sucursal)

                # Convertir a listas
                data_bbva = list(data_bbva) if data_bbva else []
                fventas_data = list(fventas_data) if fventas_data else []
                dataprose = list(dataprose) if dataprose else []

                # Diccionarios para almacenar los datos
                sucursales_data = {}
                ventas_data_dict = {}
                dataprose_data = {}

                # Función para actualizar el diccionario con la suma de abonos
                def update_data_dict(data_list):
                    for registro in data_list:
                        try:
                            fecha = registro.get('Fecha_Op', '')
                            sucursal_registro = registro['no_sucursal']
                            nom_sucur_registro = registro.get('sucursal', '')
                            nu_cuenta = registro.get('NuCuenta', '')
                            abono = float(registro['Abono'])

                            if sucursal_registro is None:
                                sucursal_registro = 'Sin sucursal'

                            key = (sucursal_registro, nom_sucur_registro)

                            if key not in sucursales_data:
                                sucursales_data[key] = {
                                    'no_sucursal': sucursal_registro,
                                    'suc': nom_sucur_registro,
                                    'data': [],
                                    'total_abonos': 0.0,
                                    'ventas': [],
                                    'porcentajes': 0.0
                                }

                            sucursales_data[key]['data'].append({
                                'Fecha_Op': fecha,
                                'no_sucursal': sucursal_registro,
                                'suc': nom_sucur_registro,
                                'NuCuenta': nu_cuenta,
                                'Abono': abono
                            })

                            sucursales_data[key]['total_abonos'] += abono

                        except KeyError as e:
                            print(f"Error de datos: {e}")
                            print(f"Registro sin clave requerida: {registro}")

                # Función para actualizar el diccionario de ventas
                def update_ventas_dict(data_list):
                    for registro in data_list:
                        try:
                            sucursal_registro = str(registro['sucursal'])
                            monto_pagado = float(registro['monto_pagado'])
                            forma_pago_id = registro['forma_pago_id']
                            fecha_c = registro['fecha']
                            origen = registro['origen']

                            if sucursal_registro is None:
                                sucursal_registro = 'Sin sucursal'

                            key = sucursal_registro

                            if key not in ventas_data_dict:
                                ventas_data_dict[key] = []

                            ventas_data_dict[key].append({
                                'sucursal': sucursal_registro,
                                'monto_pagado': monto_pagado,
                                'forma_pago_id': forma_pago_id,
                                'fecha': fecha_c,
                                'origen': origen
                            })

                        except KeyError as e:
                            print(f"Error en ventas: {e}")
                            print(f"Registro sin clave requerida: {registro}")

                # Función para actualizar el diccionario de porcentajes
                def update_porcentajes_dict(data_list):
                    for registro in data_list:
                        try:
                            sucursal_registro = str(registro['sucursal'])
                            porcentaje = float(registro['porcentaje'])

                            if sucursal_registro is None:
                                sucursal_registro = 'Sin sucursal'

                            key = sucursal_registro

                            if key not in dataprose_data:
                                dataprose_data[key] = []

                            dataprose_data[key].append({
                                'porcentaje': porcentaje
                            })

                        except KeyError as e:
                            print(f"Error en porcentajes: {e}")
                            print(f"Registro sin clave requerida: {registro}")

                # Actualizar los diccionarios con los datos combinados
                update_data_dict(data_bbva)
                update_ventas_dict(fventas_data)
                update_porcentajes_dict(dataprose)

                # Combinar los datos en el formato final
                total_abonos_por_sucursal = []
                for key, value in sucursales_data.items():
                    ventas = ventas_data_dict.get(str(value['no_sucursal']), [])

                    # Obtener los porcentajes correspondientes al no_sucursal
                    porcentajes = dataprose_data.get(str(value['no_sucursal']), [])

                    sucursal_data = {
                        'no_sucursal': value['no_sucursal'],
                        'suc': value['suc'],
                        'total_abonos': f"{value['total_abonos']:.2f}",
                        'porcentajes': porcentajes,
                        'data': value['data'],
                        'ventas': ventas
                    }
                    total_abonos_por_sucursal.append(sucursal_data)

                # Ordenar los datos por no_sucursal
                # total_abonos_por_sucursal.sort(key=lambda x: int(x['no_sucursal']) if x['no_sucursal'].isdigit() else float('inf'))
                # total_abonos_por_sucursal.sort(key=lambda x: x['no_sucursal'])
                total_abonos_por_sucursal.sort(key=lambda x: int(x['no_sucursal']) if isinstance(x['no_sucursal'], str) and x['no_sucursal'].isdigit() else 0)


                # Formatear la respuesta final
                response_data = {
                    'total_abonos_por_sucursal': total_abonos_por_sucursal
                }
                return JsonResponse(response_data, safe=False)
        else:
            conexion = conectar_bd()
            if conexion:
                fetcher = DataFetcher(conexion)
                # Obtener datos de las consultas
                data_efectivo_extracto = fetcher.dataSumExtractosEf('vistaUNO_Efectivo', fecha_inicio, fecha_fin, no_sucursal)
                data_efectivo_detalle_extracto = fetcher.dataExtractoDetalle('vistaDOS_Efectivo', fecha_inicio, fecha_fin, no_sucursal)
                # data_detalle_origen = fetcher.dataDetalleOrigen('vistaTRES_Efectivo', fecha_inicio, fecha_fin, no_sucursal)
                data_detalle_venta = fetcher.dataVentaDetalle('vistaCUATRO_Efectivo', fecha_inicio, fecha_fin, no_sucursal)
                data_extracto_venta = fetcher.dataVentaExtracto('vistaCINCO_Efectivo', fecha_inicio, fecha_fin, no_sucursal)
                
                # fventas_data = fetcher.fetch_data2('Punto_Venta', fecha_inicio, fecha_fin, no_sucursal)
                # dataprose = fetcher.fech_data5('Porsentaje_CB', fecha_inicio, fecha_fin, no_sucursal)

                # Convertir a listas
                data_efectivo_extracto = list(data_efectivo_extracto) if data_efectivo_extracto else []
                data_efectivo_detalle_extracto = list(data_efectivo_detalle_extracto) if data_efectivo_detalle_extracto else []
                #print("Data de tiendas",data_efectivo_detalle_extracto)
                data_detalle_venta = list(data_detalle_venta) if data_detalle_venta else []
                data_extracto_venta = list(data_extracto_venta) if data_extracto_venta else []
                # fventas_data = list(fventas_data) if fventas_data else []
                # dataprose = list(dataprose) if dataprose else []

                # Diccionarios para almacenar los datos
                sucursales_data = {} #declara diccionario vacio para guardad e identifcar las tiendas y no se repitan 
                ventas_data_dict = {}
                dataprose_data = {}

                # Función para actualizar el diccionario con la suma de abonos
                def update_data_dict(data_list):
                    for registro in data_list:
                        try:
                            #  DATA DE LA BD QUE VAMOS A MOSTRAR EN EL FRONT
                            NumSucursal = registro['NOSUCURSAL']
                            Sucursal = registro['NOMBRE_SUCURSAL']
                            TotalEfectivo = float(registro['TOTALEFECTIVO'])
                            FechaOp = registro['fecha']

                            if NumSucursal is None:
                                NumSucursal = 'Sin sucursal'

                            key = (NumSucursal, Sucursal) #tupla

                            if key not in sucursales_data:
                                sucursales_data[key] = {
                                    'no_sucursal': NumSucursal,
                                    'suc': Sucursal,
                                    'data': [],
                                    'total_abonos': 0.0,
                                    'ventas': [],
                                    'porcentajes': 0.0
                                }

                            sucursales_data[key]['data'].append({
                                'Fecha_Op': FechaOp,
                                'no_sucursal': NumSucursal,
                                'suc': Sucursal,
                                'NuCuenta': "",
                                'Abono': TotalEfectivo,
                                # 'total_abonos': TotalEfectivo,
                                'data': []
                            })

                            sucursales_data[key]['total_abonos'] += TotalEfectivo

                        except KeyError as e:
                            print(f"Error de datos: {e}")
                            print(f"Registro sin clave requerida: {registro}")

                # Función para actualizar el diccionario de ventas
                def update_ventas_dict(data_list):
                    for registro in data_list:
                        try:
                            sucursal_registro = str(registro['sucursal'])
                            monto_pagado = float(registro['monto_pagado'])
                            forma_pago_id = registro['forma_pago_id']
                            fecha_c = registro['fecha']
                            origen = registro['origen']

                            if sucursal_registro is None:
                                sucursal_registro = 'Sin sucursal'

                            key = sucursal_registro

                            if key not in ventas_data_dict:
                                ventas_data_dict[key] = []

                            ventas_data_dict[key].append({
                                'sucursal': sucursal_registro,
                                'monto_pagado': monto_pagado,
                                'forma_pago_id': forma_pago_id,
                                'fecha': fecha_c,
                                'origen': origen
                            })

                        except KeyError as e:
                            print(f"Error en ventas: {e}")
                            print(f"Registro sin clave requerida: {registro}")

                # Función para actualizar el diccionario de porcentajes
                def update_porcentajes_dict(data_list):
                    for registro in data_list:
                        try:
                            sucursal_registro = str(registro['sucursal'])
                            porcentaje = float(registro['porcentaje'])

                            if sucursal_registro is None:
                                sucursal_registro = 'Sin sucursal'

                            key = sucursal_registro

                            if key not in dataprose_data:
                                dataprose_data[key] = []

                            dataprose_data[key].append({
                                'porcentaje': porcentaje
                            })

                        except KeyError as e:
                            print(f"Error en porcentajes: {e}")
                            print(f"Registro sin clave requerida: {registro}")

                # Actualizar los diccionarios con los datos combinados
                update_data_dict(data_efectivo_extracto)
                
                # update_ventas_dict(fventas_data)
                # update_porcentajes_dict(dataprose)

                # Combinar los datos en el formato final
                total_abonos_por_sucursal = []
                for key, value in sucursales_data.items():
                    # ventas = ventas_data_dict.get(str(value['no_sucursal']), [])

                    # # Obtener los porcentajes correspondientes al no_sucursal
                    # porcentajes = dataprose_data.get(str(value['no_sucursal']), [])

                    sucursal_data = {
                        'no_sucursal': value['no_sucursal'],
                        'suc': value['suc'],
                        'total_abonos': f"{value['total_abonos']:.2f}",
                        'porcentajes': "",
                        'data': value['data'],
                        'ventas': ""
                    }
                    total_abonos_por_sucursal.append(sucursal_data)
                # return total_abonos_por_sucursal

                # Ordenar los datos por no_sucursal
                # total_abonos_por_sucursal.sort(key=lambda x: int(x['no_sucursal']) if x['no_sucursal'].isdigit() else float('inf'))
                # total_abonos_por_sucursal.sort(key=lambda x: x['no_sucursal'])
                total_abonos_por_sucursal.sort(key=lambda x: int(x['no_sucursal']) if isinstance(x['no_sucursal'], str) and x['no_sucursal'].isdigit() else 0)


                # Formatear la respuesta final
                response_data = {
                    'total_abonos_por_sucursal': total_abonos_por_sucursal
                }
                print(response_data)
                return JsonResponse(response_data, safe=False)
    except Exception as e:
        mensaje_error = traceback.format_exc()
        print(f"Error {mensaje_error}")
        return JsonResponse({'error': str(e)}, status=500)


    
    

@csrf_exempt
def actualizar_registros(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        idtbl_ExtractosBancarios = data.get('idtbl_ExtractosBancarios')
        ventas_sk = data.get('ventas_sk', [])

        try:
            with connection.cursor() as cursor:
                for venta_sk in ventas_sk:
                    # Intentar actualizar la tabla etlPosOne_prueba
                    cursor.execute("""
                        UPDATE etlPosOne_prueba 
                        SET idtbl_ExtractosBancarios = %s, CB = 2 
                        WHERE folio_venta = %s
                    """, [idtbl_ExtractosBancarios, venta_sk])

                    if cursor.rowcount == 0:  # Si no se actualizó ninguna fila
                        # Intentar actualizar la tabla napsepagos
                        cursor.execute("""
                            UPDATE napsepagos 
                            SET idtbl_ExtractosBancarios = %s, CB = 2 
                            WHERE Venta_sk = %s
                        """, [idtbl_ExtractosBancarios, venta_sk])

                        if cursor.rowcount == 0:  # Si tampoco se actualizó ninguna fila
                            return JsonResponse({
                                'status': 'failed',
                                'message': f'Venta_sk {venta_sk} no encontrada en ninguna tabla'
                            }, status=404)

            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)
