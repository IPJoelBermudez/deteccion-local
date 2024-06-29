from utils.modules import mysql,datetime,ET,requests,Queue,threading,HTTPDigestAuth,json,time,argparse
from utils.db_operations import *


db = mysql.connector.connect(
                            host='34.23.46.230',
                            user="root",
                             password='adnoh.1',
                             db='iparkings_camaras')

cursor = db.cursor()

def obtener_estadias_set(estadias,plate):
    for estadia in estadias:
        if estadia[1] == plate:
            return estadia

# Necesito obtener el dia actual
def dia_actual():
    # Obtener la fecha y hora actual en UTC
    fecha_actual = datetime.now()

    # Formatear la fecha y hora actual en el formato ISO 8601 con la 'Z' indicando UTC (Para los LPR)
    fecha_formateada = fecha_actual.strftime('%Y-%m-%dT')
    return fecha_formateada

def procesar_respuesta(response):
    # Obtengo la matricula
    def formater_plate(url):
        plate = ((url.split('@'))[-1].split('&')[0]).split("_")[-1]
        return plate

    # Formateado la fecha
    def formatear_fecha(date_str):
        dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    resultado = {}
    
    if response.status_code == 200:
        # Formateo la respuesta para que se pueda manipular mejor
        root = ET.fromstring(response.content)
        namespaces = {'ns0': 'http://www.hikvision.com/ver20/XMLSchema'}
        buscar_elementos = root.findall('.//ns0:searchMatchItem', namespaces)
        
        # De todos los elementos
        if buscar_elementos:
            # Voy buscando los que necesito
            for elemento in buscar_elementos:
                # Me quedo con la fecha de ingreso y la matricula
                fecha_ingreso = elemento.find('.//ns0:startTime', namespaces)
                plate = elemento.find('.//ns0:playbackURI', namespaces)
                # Formateo para que no falle
                if fecha_ingreso is not None and plate is not None:
                    matricula = formater_plate(plate.text)
                    estadia = formatear_fecha(fecha_ingreso.text)
                    resultado[matricula] = estadia
                    
    # Retorno los resultados encontrados
    return resultado

def hacer_solicitud(camara,fecha):
    username = 'admin'
    password = 'ganifox13'
    url = f'http://{camara}/ISAPI/ContentMgmt/search'
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/xml'
    }
    xml_data = f'''<CMSearchDescription>
        <searchID>CAC982E0-2400-0001-1410-12A4ECA87710</searchID>
        <trackIDList>
            <trackID>103</trackID>
        </trackIDList>
        <timeSpanList>
            <timeSpan>
                <startTime>{str(fecha)}00:00:00Z</startTime>
                <endTime>{str(fecha)}23:59:59Z</endTime>
            </timeSpan>
        </timeSpanList>
        <contentTypeList>
            <contentType>metadata</contentType>
        </contentTypeList>
        <maxResults>50</maxResults>
        <searchResultPostion>0</searchResultPostion>
        <metadataList>
            <metadataDescriptor>//recordType.meta.std-cgi.com/allPic</metadataDescriptor>
        </metadataList>
    </CMSearchDescription>'''

    response = requests.post(url, auth=HTTPDigestAuth(username, password), headers=headers, data=xml_data)
    return procesar_respuesta(response)

def leer_json(entrada, cola):
    while True:
        # Llamo al archivo camaras.json
        with open('camaras.json', 'r') as file:
            # Lo cargo
            camaras = json.load(file)
            # Busco todos los clientes
            clientes_totales = camaras.keys()
            # Voy recorriendo cliente por cliente
            for cliente in clientes_totales:
                # Tomo los lpr (ip) de entradas
                lprs = camaras[cliente][entrada]
                # Pongo los resultados en la cola
                cola.put((cliente, entrada, lprs))
                time.sleep(1)

# Crear colas
cola_in = Queue()
cola_out = Queue()

# Crear hilos y pasar las colas como argumentos
hilo_in = threading.Thread(target=leer_json, args=('In', cola_in))
hilo_out = threading.Thread(target=leer_json, args=('Out', cola_out))

# Iniciar hilos
hilo_in.start()
hilo_out.start()

# Agrego las estadias a un conjunto (Esto nos va a servir para despues cerrar la estadia)
estadias_del_dia = set()

# Leer de las colas
while True:
    # Obtengo constantemente la fecha (Para ir obteniendo los datos de la camara)
    fecha_actual = dia_actual()
    # Leer de la cola In
    if not cola_in.empty():
        print("1")
        # Recorro el resultado de cola_in
        cliente, entrada, lprs_entrada = cola_in.get()
        # Tomo todos los LPR
        for lpr_entrada in lprs_entrada:
            # Consulto las estadias de cada camara
            estadias_lpr = hacer_solicitud(lpr_entrada,fecha_actual)
            # Tomo los datos necesarios
            for plate,entrada_fecha in estadias_lpr.items():
                # Genero un barcode random 
                barcode    = str(generar_codigo_random())
                # Obtengo la id del usuario por la matricula del auto
                user_id    = obtener_id_usuario(plate,cursor)
                # Si ese usuario existe
                if user_id:
                    # Voy consultando toda su informacion
                    status_employee = obtener_status_employee(cursor,user_id)
                    parking_id = obtener_id_parking(lpr_entrada,cursor)
                    vehicle_id = obtener_id_vehicle(cursor,plate,user_id)
                    income     = 6 # Siempre sera 6 (LPR)
                    gate_in    = obtener_id_gate(cursor,lpr_entrada)
                    id_rate    = crear_id_rate(cursor,db,entrada)
                    id_item    = crear_id_item(cursor,db,barcode,id_rate,entrada)

                    # Pregunto si la estadia no existe (para que no se dupliquen)
                    if not existe_estadia(cursor,entrada_fecha,vehicle_id):
                        # Agrego la estadia
                        last_stay = agregar_estadia(
                            conn=db,
                            cursor=cursor,
                            id=id_item,
                            user=user_id,
                            employee=status_employee,
                            vehicle=vehicle_id,
                            income=income, 
                            parking=parking_id,
                            gate_in=gate_in,
                            gate_out=None,
                            DateJoin=entrada_fecha,
                            DateLeave=None,
                            enabled='1',
                            manual='0',
                            amount='0',
                            barcode=barcode,
                            alphanumericcode='V3Q',
                            url_lpr_in=lpr_entrada,
                            url_lpr_out=''
                        )
                        estadias_del_dia.add((last_stay,plate,vehicle_id,entrada_fecha))
                        print(f"Estadia creada: {last_stay},{plate},{vehicle_id},{entrada_fecha}")
                else:
                    print("No se encontraron estadias nuevas")
            
   # print(estadias_del_dia)              
    # Leer de la cola Out
    if not cola_out.empty():
        # Tomo los datos necesarios
        cliente, salida, lprs_salida = cola_out.get()
        for lpr_salida in lprs_salida:
            # Obtengo todos los datos de ese LPR
            salidas = hacer_solicitud(lpr_salida,fecha_actual)
            # Recorro las matriculas y las salidas
            for plate,DateLeave in salidas.items():
                # Busco en el SET si existe esa estadia
                estadia = obtener_estadias_set(estadias_del_dia,plate)
                # Si la encuentro tomo esos datos
                if estadia:
                    id_stay    = estadia[0] # Su id
                    id_vehicle = estadia[2] # La id del Vehiculo 
                    DateJoin   = estadia[3] # La fecha de entrada 
                    cerrar_estadia(cursor,db,id_vehicle=id_vehicle,date_in=DateJoin,DateLeave=DateLeave)
                    estadias_del_dia.discard(estadia) # Para ahorrar memoria elimino la estadia del set
                else:
                    print("Ninguna estadia fue cerrada")
                
                