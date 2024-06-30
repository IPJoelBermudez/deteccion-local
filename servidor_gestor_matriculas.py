from utils.modules import subprocess,sys,requests,HTTPDigestAuth,ET,json,socket,signal,argparse,datetime,product
from utils.logger import logger

# Variables globales
timeout = 5
server_socket = None

def obtener_fecha_actual():
    # Obtener la fecha y hora actual en UTC
    fecha_actual = datetime.now()
    # Formatear la fecha y hora en el formato ISO 8601 con la 'Z' indicando UTC
    fecha_formateada = fecha_actual.strftime('%Y-%m-%dT%H:%M:%S')
    return fecha_formateada

def enviar_respuesta(client_socket, status_code, message):
    response = f'HTTP/1.1 {status_code}\r\nContent-Type: text/plain\r\n\r\n{message}'
    client_socket.sendall(response.encode())
    logger.info(f"[RESPONSE] Enviando respuesta: {response}")

def modificar_matricula(datos):
    respuestas_camaras  = {}
    totales_modificadas = 0
    ip_camaras = list(set(datos['camaras'])) # List Set,  esto sirve para eliminar duplicados 
    new_plates = datos['new plate'] # Obtengo la matricula nueva
    old_plates = datos['old plate'] # Y la vieja (La uso para conseguir sus ids)
    plates_totales = len(new_plates) 
    ids = obtener_id_matricula(datos) # Obtengo la id de las matriculas a modificar
    for ip_camara, new_plate, old_plate, id in product(ip_camaras, new_plates, old_plates, ids): # Iterando con product, mejora el tiempo de respuesta en un 42%
        json_matricula_actualizada  = {
            "LicensePlateInfoList": [
                {
                    "LicensePlate": new_plate,
                    "listType": "whiteList",
                    "createTime": "",
                    "effectiveStartDate": "", # Saco las horas y los minutos
                    "effectiveTime": "5000-12-01",
                    "id": id
                }
            ]
        }
        try:
            # Envio la peticion put a la camara para modificar la matricula 
            consulta = requests.put(
                f"http://{ip_camara}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",
                json=json_matricula_actualizada,
                auth=HTTPDigestAuth(user, passwd),
                timeout=timeout
            )
            
            if consulta.status_code == 200:
                # Necesito obtener el total de matriculas
                totales_modificadas = totales_modificadas + 1
                # Para verificar que todas se logren modificar
                if totales_modificadas == plates_totales:
                    # Agrego la camara y si se logro modificar todo al respuestas_camaras
                    respuestas_camaras[ip_camara] = 'ok'
                    # Reseteo la variable, para que la siguiente camara puede hacer la misma comprobacion
                    totales_modificadas = 0
                    print(f"[SUCCESS] Modificación exitosa para '{old_plate}' a '{new_plate}' en {ip_camara}")
                    enviar_respuesta(client_socket, '200 OK', respuestas_camaras)
                    logger.info(f"[SUCCESS] Modificación exitosa para '{old_plate}' a '{new_plate}' en {ip_camara}")
            else:
                print(f"[ERROR] Fallo al modificar '{old_plate}' en {ip_camara}: {consulta.status_code}")
                enviar_respuesta(client_socket, '417 Expectation Failed', f'Error al modificar {old_plate}')
                logger.error(f"[ERROR] Fallo al modificar {old_plate} en {ip_camara}: {consulta.status_code}")
        
        except requests.exceptions.Timeout:
            print(f"[ERROR] El cliente {ip_camara} demoró en responder")
            enviar_respuesta(client_socket, '408 Request Timeout', f'Sin respuesta del cliente {ip_camara}')
            logger.error(f"[ERROR] El cliente {ip_camara} demoró en responder")

def obtener_id_matricula(datos):
    plate_ids = {
        'encontradas': [],
        'no_encontradas': []
    }
    ip_camaras = datos['camaras']

    # Adaptación del cuerpo de la solicitud según el caso
    if 'plates' in datos and datos['plates']:
        plates = datos['plates']
    else:
        plates = datos['old plate']
        
    for ip_camara, plate in product(ip_camaras, plates):
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <LPListAuditSearchDescription>
            <searchID>7117D5B5-7DAC-4EF2-9869-D804DDAAE201</searchID>
            <maxResults>20</maxResults>
            <searchResultPosition>0</searchResultPosition>
            <LicensePlate>{plate}</LicensePlate>
        </LPListAuditSearchDescription>"""
        url = f"http://{ip_camara}/ISAPI/Traffic/channels/1/searchLPListAudit"
        headers = {'Content-Type': 'application/xml'}
        
        try:
            response = requests.post(url, data=xml, headers=headers, auth=HTTPDigestAuth(user, passwd), timeout=timeout)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                # Verificar si hay coincidencias
                if root.find('.//{http://www.hikvision.com/ver20/XMLSchema}responseStatusStrg').text == "NO MATCHES":
                    plate_ids['no_encontradas'].append(plate)
                    print(f"[ERROR] No se encontraron IDs para {plate} en {ip_camara}")
                    logger.warning(f"[ERROR] No se encontraron IDs para {plate} en {ip_camara}")
                else:
                    for elem in root.findall('.//{http://www.hikvision.com/ver20/XMLSchema}id'):
                        plate_ids['encontradas'].append({'id': elem.text, 'plate': plate})
                        
            else:
                print(f"[ERROR] Petición para obtener datos falló: {response.status_code}")
                logger.warning(f"[ERROR] Petición para obtener datos falló: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"[ERROR] El cliente {ip_camara} demoró en responder")
            logger.error(f"[ERROR] El cliente {ip_camara} demoró en responder")

    return plate_ids

def borrar_matricula(datos):
    respuestas_camaras = {}  # Diccionario para almacenar las respuestas de las cámaras
    plates_eliminadas = 0  # Contador de matrículas eliminadas
    camaras_listas = 0  # Contador de cámaras procesadas
    ip_camaras = list(set(datos['camaras']))  # Lista de cámaras sin duplicados
    ids_dict = obtener_id_matricula(datos)  # Obtener los IDs de las matrículas
    
    # Separar matrículas encontradas y no encontradas
    ids_encontradas = ids_dict['encontradas']
    plates_no_encontradas = ids_dict['no_encontradas']
    
    total_plates = len(ids_encontradas)  # Número total de matrículas encontradas
    total_camaras = len(ip_camaras)  # Número total de cámaras

    for ip_camara, id in product(ip_camaras, ids_encontradas):
        estructura_json = {"id": [id['id']]}
        plate = id['plate']
        print(f"[DEBUGGING] Valor de la id {id}")

        url = f"http://{ip_camara}/ISAPI/Traffic/channels/1/DelLicensePlateAuditData?format=json"
        try:
            response = requests.put(url, json=estructura_json, auth=HTTPDigestAuth(user, passwd), timeout=timeout)
            if response.status_code == 200:
                print(f"[DATA DELETED] Dato eliminado: {ip_camara} {plate}")
                logger.info(f"[DATA DELETED] Dato eliminado: {ip_camara} {plate}")
                plates_eliminadas += 1  # Incrementar el contador de matrículas eliminadas

                # Si se han eliminado todas las matrículas para la cámara actual
                if plates_eliminadas == total_plates:
                    plates_eliminadas = 0  # Reiniciar el contador para la siguiente cámara
                    camaras_listas += 1  # Incrementar el contador de cámaras procesadas
                    respuestas_camaras[ip_camara] = [{'Operaciones': 'Ok'}]  # Registrar la respuesta de la cámara
                
                # Si se han procesado todas las cámaras
                if camaras_listas == total_camaras:
                    enviar_respuesta(client_socket, '200 OK', respuestas_camaras)  # Enviar la respuesta final al cliente

        except requests.exceptions.Timeout:
            enviar_respuesta(client_socket, '408 Request Timeout', f'Sin respuesta del cliente {ip_camara}')
            logger.error(f"[ERROR] El cliente {ip_camara} demoró en responder")
    
    # Manejar matrículas no encontradas
    if plates_no_encontradas:
        for plate in plates_no_encontradas:
            for ip_camara in ip_camaras:
                respuestas_camaras[ip_camara] = [{'Operaciones': 'No se encontraron matrículas', 'Plate': plate}]
        enviar_respuesta(client_socket, '404 Not Found', respuestas_camaras)
        logger.warning("[ERROR] Algunas matrículas no fueron encontradas")

    print(respuestas_camaras)


def agregar_matricula(datos):
    respuestas_camaras = {}  # Diccionario para almacenar las respuestas de las cámaras
    plates_agregadas = 0  # Contador de matrículas agregadas
    camaras_listas = 0  # Contador de cámaras procesadas
    ip_camaras = list(set(datos['camaras']))  # Lista de cámaras sin duplicados
    plates = list(set(datos['plates']))  # Lista de matrículas a agregar
    total_plates = len(plates)  # Número total de matrículas
    total_camaras = len(ip_camaras)  # Número total de cámaras

    # Iterar sobre todas las combinaciones de cámaras y matrículas
    for ip_camara, plate in product(ip_camaras, plates):  
        # Crear el JSON para la solicitud de agregar matrícula
        json_matricula_subida = {
            "LicensePlateInfoList": [{
                "LicensePlate": plate,  # Matrícula a agregar
                "listType": "whiteList",  # Tipo de lista (lista blanca)
                "createTime": f"{obtener_fecha_actual()}",  # Fecha y hora actual
                "effectiveStartDate": f"{obtener_fecha_actual().split('T')[0]}",  # Fecha de inicio de efectividad (solo fecha)
                "effectiveTime": "5000-12-01",  # Fecha de fin de efectividad
                "id": ""  # ID vacío para que sea autoincremental
            }]
        }
        
        try:
            # Enviar la solicitud PUT para agregar la matrícula
            consulta = requests.put(
                f"http://{ip_camara}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",
                json=json_matricula_subida,
                auth=HTTPDigestAuth(user, passwd),  # Autenticación digest
                timeout=timeout  # Tiempo de espera para la solicitud
            )
            
            if consulta.status_code == 200:  # Verificar si la solicitud fue exitosa
                print(f"[CLIENT] [DATA UPLOAD] Datos subidos: {ip_camara} {plate}")
                logger.info(f"[CLIENT] [DATA UPLOAD] Datos subidos: {ip_camara} {plate}")
                plates_agregadas += 1  # Incrementar el contador de matrículas agregadas

                # Si se han agregado todas las matrículas para la cámara actual
                if plates_agregadas == total_plates:  
                    plates_agregadas = 0  # Reiniciar el contador para la siguiente cámara
                    camaras_listas += 1  # Incrementar el contador de cámaras procesadas
                    respuestas_camaras[ip_camara] = [{'Operaciones': 'Ok'}]  # Registrar la respuesta de la cámara
                    #print(f"[DEBUGGING] Variable total_camaras = {camaras_listas}")

                # Si se han procesado todas las cámaras
                if camaras_listas == total_camaras:
                    enviar_respuesta(client_socket, '200 OK', respuestas_camaras)  # Enviar la respuesta final al cliente
        
            else:
                # Manejo de error si la solicitud falla
                #print(f"[CLIENT] [ERROR DATA UPLOAD] Fallo al subir {plate} en {ip_camara}: {consulta.status_code}")
                enviar_respuesta(client_socket, '417 Expectation Failed', f'Error al subir {plate}')
                logger.error(f"[CLIENT] [ERROR DATA UPLOAD] Fallo al subir {plate} en {ip_camara}: {consulta.status_code}")
        
        except requests.exceptions.Timeout:
            # Manejo de error si la solicitud excede el tiempo de espera
            print(f"[CLIENT] [ERROR] El cliente {ip_camara} demoró en responder")
            enviar_respuesta(client_socket, '408 Request Timeout', f'Sin respuesta del cliente {ip_camara}')
            logger.error(f"[CLIENT] [ERROR] El cliente {ip_camara} demoró en responder")

def obtener_datos(request):
    headers = request.split('\r\n')
    if headers[0].startswith('POST'):
        action_post = headers[0].split(" ")[1]
        idx = request.find('\r\n\r\n')
        if idx != -1:
            body = request[idx + 4:]
            try:
                data_camaras = json.loads(body)
                print(f"[CLIENT] [DATA RECEIVED] Datos recibidos: {data_camaras}")
                logger.info(f"[CLIENT] [DATA RECEIVED] Datos recibidos: {data_camaras}")
                return data_camaras, action_post
            except json.JSONDecodeError as e:
                print(f"[SERVER] [ERROR] JSON mal formado: {e}")
                enviar_respuesta(client_socket, '400 Bad Request', 'JSON mal formado')
                logger.error(f"[ERROR] JSON mal formado: {e}")
        else:
            print("[SERVER] [ERROR] Cuerpo de solicitud no encontrado")
            enviar_respuesta(client_socket, '400 Bad Request', 'Cuerpo de solicitud no encontrado')
            logger.error("[SERVER] [ERROR] Cuerpo de solicitud no encontrado")
    else:
        print("[SERVER] [ERROR] Método no permitido")
        logger.error("[SERVER] [ERROR] Método no permitido")

    return None, None

def manejar_solicitud(client_socket):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        logger.info(f"[REQUEST] Solicitud recibida: {request}")
        data,action = obtener_datos(request)
        if data:
            if action == '/AddPlate': # Agregar 
                agregar_matricula(data)
            
            elif action == '/UpdatePlate': # Actualizar
                modificar_matricula(data)

            elif action == '/DeletePlate': # Eliminar
                borrar_matricula(data)
            else:
                print("[ERROR] Operación no reconocida")
                enviar_respuesta(client_socket, '400 Bad Request', 'Operación no reconocida')
                logger.error("[ERROR] Operación no reconocida")
        
        else: # Si el metodo no es el correcto
            print("[ERROR] Al obtener datos")
            # Envio una respuesta
            enviar_respuesta(client_socket, '405 Method Not Allowed', 'Metodo no permitido')
            logger.error("[ERROR] Operación no reconocida")
    
    except Exception as e:
        enviar_respuesta(client_socket, '500 Internal Server Error', 'Error del servidor')
        print("[ERROR] Error del servidor: ", e)
        logger.exception("[ERROR] Error del servidor: ", e)

    finally: # Para cubrir otros errores, cuando algo falla cierro la conexion con el cliente
        client_socket.close()

def iniciar_servidor():
    global server_socket,client_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM Para que use TCP
                                                                      # AF_INET Para direcciones IPv4
    server_socket.bind(('', PUERTO))
    server_socket.listen(4) # Permito maximo 4 conexiones
    print(f"[SERVER STARTED] Servidor escuchando en el puerto {PUERTO}")
    logger.info(f"[SERVER STARTED] Servidor escuchando en el puerto {PUERTO}")
    while True:
        client_socket, addr = server_socket.accept()
        print(f"[CONNECTION ACCEPTED] Conexión aceptada de {addr}")
        logger.info(f"[CONNECTION ACCEPTED] Conexión aceptada de {addr}")
        manejar_solicitud(client_socket)

def signal_handler(sig, frame):
    print(f"[SERVER STOPPED] Servidor detenido")
    logger.info("[SERVER STOPPED] Servidor detenido")
    if server_socket:
        server_socket.close()
    sys.exit(0)

def main():
    global user, passwd, PUERTO
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, help='Nombre de usuario')
    parser.add_argument('-c', '--passwd', required=True, help='Contraseña')
    parser.add_argument('-p', '--port', required=False,default=8080, help='Puerto')
    args = parser.parse_args()
    user = args.user
    passwd = args.passwd
    PUERTO = int(args.port)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    iniciar_servidor()

if __name__ == '__main__':
    main()
