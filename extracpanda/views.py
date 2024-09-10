from django.shortcuts import redirect,render
from django.http import JsonResponse
import pandas as pd
import pymysql
from pymysql import connect, cursors
from datetime import datetime
from django.http import JsonResponse
import paramiko
from django.db import connections, connection, DatabaseError
import json
import locale
import logging
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.urls import reverse
import traceback
from django.utils.http import urlencode
import openpyxl
from django.views.decorators.csrf import csrf_protect
from dateutil  import parser
import re


def conectar_bd():
     try:
          db = pymysql.connect(
               host='uat.consolidacionbancaria.mobo.com.mx',
            #    user='UserCB',
               user= 'jesanchez',
               password = 'moboweb5226',
            #    password='DevCB',
               database='consolidacion',
               cursorclass=cursors.DictCursor,
               autocommit=True
            )
          return db
     except Exception as e:
          logging.error("Error al conectar a la base de datos: %s", e)
          return None
     
def vistaExtracto(request):
    return render(request, 'extracpanda/index.html')

def menu(request):
    return render(request, 'extracpanda/base2.html')

def tablas(request):
    return render(request, 'extracpanda/tablas.html')

def TablaIvan(request):
    return render(request, 'extracpanda/select_columns2_Ivan.html')

def select_columns2(request):
    try:
        # Recupera los datos de la sesión
        columns = request.session.get('columns', [])
        rows = request.session.get('rows', [])

        # Verifica que haya datos disponibles
        if not columns or not rows:
            return render(request, 'extracpanda:error.html', {'error_message': 'No hay datos disponibles'})

        # Resto del código para procesar y mostrar los datos en el template

        return render(request, 'extracpanda/select_columns2.html', {'columns': columns, 'rows': rows})
    except Exception as e:
        # Manejo de errores
        return render(request, 'extracpanda:error.html', {'error_message': str(e)})

def select_columnsAmex(request):
    return render(request, 'extracpanda/select_columnsAmex.html')
# funcion para limpiar los datos del excel
def limpiar_datos(df):
   for columna in df.columns:
        if df[columna].dtype == 'object':
            df[columna] = df[columna].str.replace("'", "")
   return df

# funciones nuevas para cargar los ETL de los bancos
# funciones para extraer las columnas de cada banco
# funciones de para extractos bancarios de efectivo
@csrf_exempt
def cargar_excel_azteca(uploaded_file, select_option):
    try:
        logging.info(f'Cargar archivo Banco Azteca: {uploaded_file.name}')
        print(f'Selected Option Banco Azteca (cargar_excel_azteca): {select_option}')

        df = pd.read_excel(uploaded_file, engine='openpyxl')

        # funcion para limpiar datos
        df = limpiar_datos(df)
        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: { num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe esta vacio desde la funcion")
            return{'success': False, 'message': 'El dataframe esta vacio'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de Azteca: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

@csrf_exempt
def cargar_excel_coppelV2(uploaded_file, selected_option):
    try:
        logging.info(f'Cargar archivo coppel: {uploaded_file.name}')
        print(f"Selected Option coppel(cargar_excel_coppel): {selected_option}")

        # Leer el archivo Excel y seleccionar las columnas A a D
        df = pd.read_excel(uploaded_file, engine='openpyxl', header=2, usecols="A:D")
        
        # Obtener el valor de la celda D1 y asignarlo a la nueva columna 'Cuenta'
        valor_celda_d1 = pd.read_excel(uploaded_file, engine='openpyxl', usecols="D", nrows=1, header=None).iloc[0,0]
        df['Cuenta'] = valor_celda_d1

        # Convertir la columna 'Importe' a tipo numérico (eliminando las comas)
        df['Importe'] = df['Importe'].replace(',', '', regex=True).astype(float)

        # Crear las columnas 'Cargo' y 'Abono' basándonos en los valores de 'Importe'
        df['Cargo'] = df['Importe'].apply(lambda x: x if x < 0 else None)
        df['Abono'] = df['Importe'].apply(lambda x: x if x >= 0 else None)

        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe esta vacio")
            return {'success': False, 'message': 'El dataframe esta vacio'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de coppel: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

@csrf_exempt
def carga_excel_inbursa(uploaded_file, selected_option):
    try:
        logging.info(f'Carga archivo Inbursa: {uploaded_file.name}')
        print(f"Selected Option inbursa (cargar_excel_inbursa): {selected_option}")

        df = pd.read_excel(uploaded_file, engine='openpyxl', header=5, usecols="A:K")

        # Buscar la cadena "Cuenta Cargo:036180500182063375" en el archivo Excel
        with pd.ExcelFile(uploaded_file) as xls:
            valor_celda_a3 = None
            for sheet_name in xls.sheet_names:
                df_temp = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                for row in df_temp.iterrows():
                    if row[1][0] == "Cuenta Cargo:036180500182063375":
                        valor_celda_a3 = row[1][0].split(":")[1].strip()
                        break
                if valor_celda_a3:
                    break

        if valor_celda_a3:
            df['Cuenta'] = valor_celda_a3
        else:
            logging.warning("No se encontró la cadena 'Cuenta Cargo:036180500182063375' en el archivo Excel.")

        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: {num_registros}")
            return {'success':True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe está vacío.")
            return {'success': False, 'message': 'El dataframe está vacío'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de Inbursa: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

@csrf_exempt
def cargar_excel_mifilV2(uploaded_file,  selected_option):
    try:
        logging.info(f'Cargar archivo mifil: {uploaded_file.name}')
        print(f"Selected Option mifil (cargar_excel_mifil): {selected_option}")
        df = pd.read_csv(uploaded_file, skiprows=10, encoding='latin-1')
        
        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe esta vacio")
            return{'success': False, 'message': 'El dataframe esta vacio'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de mifil: {str(e)}"
        logging.error(error_message)
        return{'success': False, 'message': error_message}

@csrf_exempt
def cargar_excel_santander(uploaded_file, selected_option):
    try:
        logging.info(f'Cargar archivo Santander: {uploaded_file.name}')
        print(f"Selected Option Santander (cargar_excel_santander): {selected_option}")
        df = pd.read_excel(uploaded_file, engine='openpyxl')

        # Limpiar los registros y quitar las comillas simples de los datos
        df = df.applymap(lambda x: x.strip("'") if isinstance(x, str) else x)

        df['Cargo'] = df.apply(lambda row: row['Importe'] if row['Cargo/Abono'] == '-' else 0, axis=1)
        df['Abono'] = df.apply(lambda row: row['Importe'] if row['Cargo/Abono'] == '+' else 0, axis=1)
        
        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe está vacío.")
            return {'success': False, 'message': 'El dataframe está vacío'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de Santander: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

@csrf_exempt
def carga_bbvaefectivo(uploaded_file, select_option):
    try:
        logging.info(f'Cargar archivo bbva efectivo: {uploaded_file.name}')
        print(f'Opción seleccionada bbva efectivo: {select_option}')
        
        # Leer el archivo Excel sin omitir ninguna fila
        df = pd.read_excel(uploaded_file, engine='openpyxl', header=None)
        cuenta = df.iloc[0, 1]
        df.columns = df.iloc[1]
        df = df.iloc[2:]
        df['Cuenta'] = cuenta
        # return df
        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNúmero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe está vacío")
            return {'success': False, 'message': 'El dataframe está vacío'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de bbva efectivo: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

@csrf_exempt
def QAefectivo(uploaded_file, select_option):
    try:
        logging.info(f'Cargar archivo bbva efectivo: {uploaded_file.name}')
        print(f'Opción seleccionada bbva efectivo: {select_option}')
        
        # Leer el archivo Excel sin omitir ninguna fila
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl', header=None)
        except ValueError as ve:
            error_message = f"Error al leer el archivo Excel: {str(ve)}"
            logging.error(error_message)
            return {'success': False, 'message': error_message}

        cuenta = df.iloc[0, 1]
        df.columns = df.iloc[1]
        df = df.iloc[2:]
        df['Cuenta'] = cuenta

        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNúmero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe está vacío")
            return {'success': False, 'message': 'El dataframe está vacío'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de bbva efectivo: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}


@csrf_exempt
def cargar_bnmx(uploaded_file, selected_option):
    try:
        logging.info(f'Cargar archivo Bbva: {uploaded_file.name}')
        print(f"Selected Option bbva (cargar_excel_bbva): {selected_option}")

        df = pd.read_excel(uploaded_file, engine='openpyxl')

        valor_celda_e4 = df.iloc[2, 4]

        df = pd.read_excel(uploaded_file, skiprows=14, engine='openpyxl')

        df['Cuenta'] = valor_celda_e4

        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNúmero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe está vacío.")
            return {'success': False, 'message': 'El dataframe está vacío'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de BBVA: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}


@csrf_exempt
def cargar_excel_hsbc_efec(uploaded_file, select_option):
    try:
        global df
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        if not df.empty:
            return {"status": "success", "dataframe": df}
        else:
            return{"status": "error", "message": "El dataframe esta vacio"}
        # print("columnas del dataframe hsbc", df.columns)
        # df = df[['Saldo actual disponible', 'Referencia bancaria', 'Descripción', 'Referencia de cliente', 'Tipo de TRN', 'Hora de cargo o abono']]
        # return None
    except Exception as e:
        return f"Error al cargar el archivo Excel hsbc: {str(e)}"

@csrf_exempt
def cargar_excel_scotia(uploaded_file, selected_option):
    try:
        logging.info(f'Cargar archivos Scotia: {uploaded_file.name}')
        print(f"Selected Option scotia (cargar_excel_scotia): {selected_option}")
        df = pd.read_excel(uploaded_file, engine='openpyxl')

        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe esta vacio.")
            return {'success': False, 'message': 'El dataframe esta vacio'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de scotia"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

def cargar_excel_cibanco(uploaded_file, selected_option):
    try:
        logging.info(f'Cargar archivo cibanco: {uploaded_file.name}')
        print(f"Selected Option cibanco(cargar_cibanco): {selected_option}")

        df = pd.read_excel(uploaded_file, engine='openpyxl')
        cuenta = df.iloc[0,1]
        df.columns = df.iloc[1]
        df = df.iloc[2:]
        df['Cuenta'] = cuenta

        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: {num_registros}")
            return{'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe esta vacio")
            return{'success': False, 'message': 'El dataframe esta vacio'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de cibanco: {str(e)}"
        logging.error(error_message)
        return{'success': False, 'message': error_message}

# funciones para extractos bancarios de tarjetas
@csrf_exempt
# esta funcion sirve para el extracto bancario para las cuentas 
def cargar_excel_bbva(uploaded_file, selected_option):
    try:
        logging.info(f'Cargar archivo Bbva: {uploaded_file.name}')
        print(f"Selected Option bbva (cargar_excel_bbva): {selected_option}")
        df = pd.read_excel(uploaded_file, engine='openpyxl')

        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNúmero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe está vacío.")
            return {'success': False, 'message': 'El dataframe está vacío'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de BBVA: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

@csrf_exempt
def amex_com(uploaded_file, selected_option):
    try:
        logging.info(f'Cargar archivo amex complemento: {uploaded_file.name}')
        print(f"Selected Option amex complemento (cargar_amex): {selected_option}")
        df = pd.read_excel(uploaded_file, engine='openpyxl', skiprows=17)
        if df is not None and not df.empty:
            logging.info("Registros cargados en el dataframe:")
            logging.info(df.head())

            num_registros = len(df)
            logging.info(f"\nNumero de registros: {num_registros}")
            return {'success': True, 'dataframe': df, 'num_registros': num_registros}
        else:
            logging.warning("El dataframe estaa vacio.")
            return {'success': False, 'message': 'El dataframe esta vacio'}
    except Exception as e:
        error_message = f"Error al cargar el archivo de amex complemento: {str(e)}"
        logging.error(error_message)
        return {'success': False, 'message': error_message}

@csrf_exempt
def amex_complemento(file):
    global num_registros
    try:
        global df
        df = pd.read_excel(file, engine='openpyxl', skiprows=17)
        if not df.empty:
            print("Registros cargados en el dataframe:")
            print(df.head())
            num_registros = len(df)
            print("\nNumero de registros", num_registros)
            return {"status": "success", "dataframe": df}
        else:
            print("El dataframe está vacío")
            return {"status": "error", "message": "El dataframe está vacío"}
    except Exception as e:
        print(f"Error al cargar el archivo de AMEX: {str(e)}")
        return {"status": "error", "message": f"Error al cargar el archivo de AMEX: {str(e)}"}

@csrf_exempt
def cargar_excel_hsbc(uploaded_file, selected_option):
   try:
       logging.info(f'Cargar archivo hsbc efectivo: {uploaded_file.name}')
       print(f"Selecte Option hsbc (cargar_excel_hsbc): {selected_option}")
       df = pd.read_excel(uploaded_file, engine='openpyxl')
       if df is not None and not df.empty:
           logging.info("Registros cargados en el dataframe:")
           logging.info(df.head())

           num_registros = len(df)
           logging.info(f"\nNumero de registros: {num_registros}")
           return {'success' : False, 'dataframe': df, 'num_registros': num_registros}
       else:
           logging.warning("El dataframe esta vacio.")
           return {'success': False, 'message': 'El dataframe esta vacio'}
   except Exception as e:
       error_message = f"Error al cargar el archivo de efectivo hsbc: {str(e)}"
       logging.error(error_message)
       return{'success': False, 'message': error_message}


@csrf_protect
def update_option(request):
    result_message = {}
    selected_type = None
    selected_option = None

    try:
        selected_type = request.POST.get('tipo_operacion')

        if selected_type == 'efectivo':
            selected_option = request.POST.get('excel_format_efectivo')
            uploaded_file = request.FILES.get('file')

            if selected_option == 'opcion_efectivo_1': #azteca (9774)
                result_message = cargar_excel_azteca(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_2': # bbva (9530)
                result_message = carga_bbvaefectivo(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_3': # bbva (9474)
                result_message = QAefectivo(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_4': #coppel (9391)
                result_message = cargar_excel_coppelV2(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_5': #santander (3790)
                result_message = cargar_excel_santander(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_6': # cibanco (7403)
                result_message = cargar_excel_cibanco(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_7':# hsbc (3260)
                result_message = cargar_excel_hsbc_efec(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_8': #inbursa (6337)
                result_message = carga_excel_inbursa(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_9':# banamex (0407)
                result_message = cargar_bnmx(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_10':# scotiaback (2883)
                result_message = cargar_excel_scotia(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_11': #bbva (9557)
                result_message = carga_bbvaefectivo(uploaded_file, selected_option)
            elif selected_option == 'opcion_efectivo_12': # banamex (7867)
                result_message = cargar_bnmx(uploaded_file, selected_option)
            

        elif selected_type == 'tarjeta':
            selected_option = request.POST.get('excel_format_tarjeta')
            uploaded_file = request.FILES.get('file')
            if selected_option == 'opcion_tarjeta_1':
                result_message = cargar_excel_bbva(uploaded_file, selected_option) 
            elif selected_option == 'opcion_tarjeta_2':
                result_message = cargar_excel_hsbc(uploaded_file, selected_option)

        elif selected_type == 'amexplus':
            selected_option = request.POST.get('amex')
            uploaded_file = request.FILES.get('file')
            if selected_option == 'amex_plus':
                result_message = amex_com(uploaded_file, selected_option)
            else:
                return JsonResponse({'status': 'error', 'message': 'Tipo de operación no válido'}, status=400)
        
        print(f"Debug: result_message={result_message}")

        if result_message.get('status') == 'error':
            return JsonResponse(result_message, status=400)

        if result_message:
            df = result_message.get('dataframe')

            if df is not None:
                rows = df.to_dict(orient='records')

                if selected_type == 'efectivo':
                    df = result_message.get('dataframe')
                    if df is not None:
                        rows = df.to_dict(orient='records')
                        context = {'columns': df.columns.tolist(), 'rows': rows}
                        return render(request, 'extracpanda/select_columnsEfect.html', context)
                    else:
                        return JsonResponse({'status': 'error', 'message': 'El dataframe no None despues de la carga'}, status=500)
                elif selected_type == 'tarjeta':
                    return render(request, 'extracpanda/select_columns2.html', {'columns': df.columns.tolist(), 'rows': rows})
                    # return redirect({'action': 'render', 'template': 'extracpanda/select_columns2.html', 'columns': df.columns.tolist(), 'rows': rows})
                elif selected_type == 'amexplus':
                    return render(request, 'extracpanda/select_columnsAmex.html', {'columns': df.columns.tolist(), 'rows': rows})
                    # return redirect({'action': 'render', 'template': 'extracpanda/select_columnsAmex.html', 'columns': df.columns.tolist(), 'rows': rows})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Tipo de operación no válido'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': 'El DataFrame es None despues de la carga'}, status=500)
        else:
            return JsonResponse({'status': 'error', 'message': 'result_message es None'}, status=500)
    except Exception as e:
        print(traceback.format_exc())
        error_message = f"Error en la función update: {str(e)}"
        print(error_message)
        return JsonResponse({'status': 'error', 'message': error_message}, status=500)
    # return JsonResponse({'status': 'error', 'message': 'Error inesperado, no se pudo procesar la solicitud'}, status=500)

    
# DB_NAME = 'bancos.db'
# TABLE_NAME = 'bank'

# Configura la conexión a la base de datos "solo fue de prueba"
db = pymysql.connect(host='40.124.171.87', user='jesanchez', password='moboweb5226', database='consolidacion', cursorclass=cursors.DictCursor )
cursor = db.cursor()

logger = logging.getLogger(__name__)


@csrf_exempt
# def formatear_fecha(fecha_str):
#     print(f"Fecha original: {fecha_str}")

#     # Definir los meses en español para validación
#     meses = {
#         "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
#         "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
#     }

#     try:
#         # Intentar parsear la fecha con el formato "dd/mm/yyyy"
#         fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
#         # Cambiar el formato al deseado ('YYYY-MM-DD')
#         fecha_formateada = fecha_dt.strftime('%Y-%m-%d')
#         return fecha_formateada
#     except ValueError:
#         # Expresión regular para detectar diferentes formatos de fecha
#         regex = r'(?P<dia>\d{1,2}) de (?P<mes>\w+) de (?P<anio>\d{4})'
#         regex_dmy = r'(?P<dia>\d{2})(?P<mes>\d{2})(?P<anio>\d{4})'

#         match = re.match(regex, fecha_str)
#         if match:
#             dia = int(match.group('dia'))
#             mes = meses.get(match.group('mes').lower(), None)
#             anio = int(match.group('anio'))
#             if mes is not None and 1 <= dia <= 31:
#                 fecha_formateada = f"{anio:04d}-{mes:02d}-{dia:02d}"
#                 return fecha_formateada

#         match_dmy = re.match(regex_dmy, fecha_str)
#         if match_dmy:
#             dia = int(match_dmy.group('dia'))
#             mes = int(match_dmy.group('mes'))
#             anio = int(match_dmy.group('anio'))
#             try:
#                 fecha_dt = datetime(year=anio, month=mes, day=dia)
#                 fecha_formateada = fecha_dt.strftime('%Y-%m-%d')
#                 return fecha_formateada
#             except ValueError:
#                 pass

#         print(f"Error al formatear la fecha: Formato no válido - {fecha_str}")
#         return None

# funcion 2
def formatear_fecha(fecha_str):
    print(f"Fecha original: {fecha_str}")

    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str):
        return fecha_str
    
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    try:
        fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
        fecha_formateada = fecha_dt.strftime('%Y-%m-%d')
        return fecha_formateada
    except ValueError:
        regex = r'(?P<dia>\d{1,2}) de (?P<mes>\w+) de (?P<anio>\d{4})'
        regex_dmy = r'(?P<dia>\d{2})(?P<mes>\d{2})(?P<anio>\d{4})'

        match = re.match(regex, fecha_str)
        if match:
            dia = int(match.group('dia'))
            mes = meses.get(match.group('mes').lower(), None)
            anio = int(match.group('anio'))
            if mes is not None and 1 <= dia <= 31:
                fecha_formateada = f"{anio:04d}-{mes:02d}-{dia:02d}"
                return fecha_formateada
        
        match_dmy = re.match(regex_dmy, fecha_str)
        if match_dmy:
            dia = int(match_dmy.group('dia'))
            mes = int(match_dmy.group('mes'))
            anio = int(match_dmy.group('anio'))
            try:
                fecha_dt = datetime(year=anio, month=mes, day=dia)
                fecha_formateada = fecha_dt.strftime('%Y-%m-%d')
                return fecha_formateada
            except ValueError:
                pass
        print(f"Error al formatear la fecha: Formato no valido - {fecha_str}")
        return None

    

@csrf_exempt
def enviar_route(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        if not data:
            return JsonResponse({'success': False, 'message': 'No se recibieron datos en la solicitud'}, status=400)

        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.utf-8')
            # Resto del código que requiere la configuración regional
        except Exception as e:
            print(f"Error al establecer la configuración regional: {str(e)}")
        finally:
            locale.setlocale(locale.LC_ALL, '')

        with conectar_bd() as connection:
            if connection is None:
                return JsonResponse({'success': False, 'message': 'No se pudo establecer la conexión a la base de datos'}, status=500)
            with connection.cursor() as cursor:
                for banco_data in data.get('banco', []):
                    numero_cuenta = banco_data.get('Banco', '').split('\n')
                    fecha_operacion = banco_data.get('Fecha Operacion', '').split('\n')
                    tipo_trans_valor = banco_data.get('Tipo de Transacción', '').split('\n')
                    ref_ampl_valor = banco_data.get('Referencia Ampliada', '').split('\n')
                    no_cl_valor = banco_data.get('No. Campo de Llave', '').split('\n')
                    abono_valor = banco_data.get('Abono', '').split('\n')
                    cargo_valor = banco_data.get('Cargo', '').split('\n')

                    # Asegura que todas las listas tengan la misma longitud
                    max_length = max(len(numero_cuenta), len(fecha_operacion), len(tipo_trans_valor), len(ref_ampl_valor), len(no_cl_valor), len(abono_valor), len(cargo_valor))
                    numero_cuenta += [''] * (max_length - len(numero_cuenta))
                    fecha_operacion += [''] * (max_length - len(fecha_operacion))
                    tipo_trans_valor += [''] * (max_length - len(tipo_trans_valor))
                    ref_ampl_valor += [''] * (max_length - len(ref_ampl_valor))
                    no_cl_valor += [''] * (max_length - len(no_cl_valor))
                    abono_valor += [''] * (max_length - len(abono_valor))
                    cargo_valor += [''] * (max_length - len(cargo_valor))

                    # abono_valor = [float(valor.replace(',', '.')) if valor != 'nan' else None for valor in abono_valor]
                    # cargo_valor = [float(valor.replace(',', '.')) if valor != 'nan' else None for valor in cargo_valor]
                    # nuevo 
                    abono_valor = [float(valor.replace(',', '.')) if valor.strip() and valor != 'nan' else None for valor in abono_valor]
                    cargo_valor = [float(valor.replace(',', '.')) if valor.strip() and valor != 'nan' else None for valor in cargo_valor]
                    if max_length > 0:
                        print(f"Registros a insertar en la base de datos")
                        print(f"Número de registros a insertar: {max_length}")

                        for i in range(max_length):
                            # print(f"NuCuenta: {numero_cuenta[i]}, Fecha_Op: {fecha_operacion[i]}, Tipo_trans: {tipo_trans_valor[i]}, Ref_ampl: {ref_ampl_valor[i]}, No_CL: {no_cl_valor[i]}, Abono: {abono_valor[i]}, Cargo: {cargo_valor[i]}")
                            print(f"NuCuenta: {numero_cuenta[i]}, Fecha_Op: {fecha_operacion[i]}, Tipo_trans: {tipo_trans_valor[i]}, Ref_ampl: {ref_ampl_valor[i]}, No_CL: {no_cl_valor[i]}, Abono: {abono_valor[i]}, Cargo: {cargo_valor[i]}")

                            # Formatear la fecha_operacion_i si es necesario
                            fecha_operacion_formatted = None
                            if fecha_operacion[i]:
                                try:
                                    fecha_operacion_dt = formatear_fecha(fecha_operacion[i])
                                    fecha_operacion_formatted = fecha_operacion_dt
                                except ValueError as e:
                                    print(f"Error al formatear la fecha: {str(e)}")

                            if fecha_operacion_formatted is not None:
                                query = 'INSERT INTO Insertar_QA(NuCuenta, Fecha_Op, Tipo_trans, Ref_ampl, No_Cl, Abono, Cargo) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                                values = (numero_cuenta[i], fecha_operacion_formatted, tipo_trans_valor[i], ref_ampl_valor[i], no_cl_valor[i], abono_valor[i], cargo_valor[i])
                                if abono_valor[i] != 'nan':
                                    try:
                                        cursor.execute(query, values)
                                    except Exception as e:
                                        # Manejar el error según sea necesario
                                        print(f"Error en la consulta para el índice {i}: {str(e)}")

                        # Commit y cerrar la conexión
                        connection.commit()

                        return JsonResponse({'success': True, 'message': 'Datos insertados correctamente'})
                    else:
                        print(f"El número de registros a insertar ({max_length}) no coincide con el número de registros cargados. No se realizará la inserción.")
                        return JsonResponse({'success': False, 'message': 'Error: El número de registros a insertar no coincide con el número de registros cargados'}, status=400)
                else:
                    print(f"No hay registros a insertar")
                    return JsonResponse({'success': True, 'message': 'No hay registros a insertar'}, status=200)
    except Exception as e:
        print(f'Error al procesar la solicitud: {str(e)}')
        connection.rollback()
        return JsonResponse({'success': False, 'message': f'Error al procesar la solicitud: {str(e)}'}, status=500)
    


@csrf_exempt
def amex(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        if not data:
            return JsonResponse({'success': False, 'message': 'No se recibieron datos en la solicitud'}, status=400)

        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.utf-8')
            # Resto del código que requiere la configuración regional
        except Exception as e:
            print(f"Error al establecer la configuración regional: {str(e)}")
        finally:
            locale.setlocale(locale.LC_ALL, '')

        with conectar_bd() as connection:
            if connection is None:
                return JsonResponse({'success': False, 'message': 'No se pudo establecer la conexión a la base de datos'}, status=500)
            with connection.cursor() as cursor:
                for banco_data in data.get('banco', []):
                    numero_cuenta = banco_data.get('Banco', '').split('\n')
                    fecha_operacion = banco_data.get('Fecha Operacion', '').split('\n')
                    tipo_trans_valor = banco_data.get('Tipo de Transacción', '').split('\n')
                    ref_ampl_valor = banco_data.get('Referencia Ampliada', '').split('\n')
                    no_cl_valor = banco_data.get('No. Campo de Llave', '').split('\n')
                    abono_valor = banco_data.get('Abono', '').split('\n')
                    cargo_valor = banco_data.get('Cargo', '').split('\n')

                    # Asegura que todas las listas tengan la misma longitud
                    max_length = max(len(numero_cuenta), len(fecha_operacion), len(tipo_trans_valor), len(ref_ampl_valor), len(no_cl_valor), len(abono_valor), len(cargo_valor))
                    numero_cuenta += [''] * (max_length - len(numero_cuenta))
                    fecha_operacion += [''] * (max_length - len(fecha_operacion))
                    tipo_trans_valor += [''] * (max_length - len(tipo_trans_valor))
                    ref_ampl_valor += [''] * (max_length - len(ref_ampl_valor))
                    no_cl_valor += [''] * (max_length - len(no_cl_valor))
                    abono_valor += [''] * (max_length - len(abono_valor))
                    cargo_valor += [''] * (max_length - len(cargo_valor))

                    if max_length > 0:
                        print(f"Registros a insertar en la base de datos")
                        print(f"Número de registros a insertar: {max_length}")

                        for i in range(max_length):
                            print(f"NuCuenta: {numero_cuenta[i]}, Fecha_Op: {fecha_operacion[i]}, Tipo_trans: {tipo_trans_valor[i]}, Ref_ampl: {ref_ampl_valor[i]}, No_CL: {no_cl_valor[i]}, Abono: {abono_valor[i]}, Cargo: {cargo_valor[i]}")

                            # Formatear la fecha_operacion_i si es necesario
                            fecha_operacion_formatted = None
                            if fecha_operacion[i]:
                                try:
                                    # locale.setlocale(locale.LC_ALL, 'es_ES.utf-8')
                                    fecha_operacion_dt = formatear_fecha(fecha_operacion[i])
                                    fecha_operacion_formatted = fecha_operacion_dt
                                except ValueError as e:
                                    print(f"Error al formatear la fecha: {str(e)}")

                            if fecha_operacion_formatted is not None:
                                query = 'INSERT INTO TempExtractosBancarios (NuCuenta, Fecha_Op, Tipo_trans, Ref_ampl, No_Cl, Abono, Cargo) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                                values = (numero_cuenta[i], fecha_operacion_formatted, tipo_trans_valor[i], ref_ampl_valor[i], no_cl_valor[i], abono_valor[i], cargo_valor[i])

                                try:
                                    cursor.execute(query, values)
                                except Exception as e:
                                    # Manejar el error según sea necesario
                                    print(f"Error en la consulta para el índice {i}: {str(e)}")

                        # Commit y cerrar la conexión
                        connection.commit()

                        return JsonResponse({'success': True, 'message': 'Datos insertados correctamente'})
                    else:
                        print(f"El número de registros a insertar ({max_length}) no coincide con el número de registros cargados. No se realizará la inserción.")
                        return JsonResponse({'success': False, 'message': 'Error: El número de registros a insertar no coincide con el número de registros cargados'}, status=400)
                else:
                    print(f"No hay registros a insertar")
                    return JsonResponse({'success': True, 'message': 'No hay registros a insertar'}, status=200)
    except Exception as e:
        print(f'Error al procesar la solicitud: {str(e)}')
        connection.rollback()
        return JsonResponse({'success': False, 'message': f'Error al procesar la solicitud: {str(e)}'}, status=500)