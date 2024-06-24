from utils.modules import subprocess,sys,requests,HTTPDigestAuth,ET,json,socket,signal,argparse,datetime
from utils.logger import logger

# Lista de dependencias
dependencies = ["requests"]

def install_dependencies(packages):
    """Instala las dependencias usando pip"""
    import pip
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"[INSTALLING] Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies(dependencies)

# Variables globales para el usuario, la contraseña y el puerto
user = None
passwd = None
PUERTO = None
server_socket = None

def obtener_fecha_actual():
    # Obtener la fecha y hora actual en UTC
    fecha_actual = datetime.now(datetime.UTC)
    # Formatear la fecha y hora en el formato ISO 8601 con la 'Z' indicando UTC
    fecha_formateada = fecha_actual.strftime('%Y-%m-%dT%H:%M:%SZ')
    return fecha_formateada

def enviar_respuesta(client_socket, status_code, message):
    response = f'HTTP/1.1 {status_code}\r\nContent-Type: text/plain\r\n\r\n{message}'
    client_socket.sendall(response.encode())
    logger.info(f"[RESPONSE] Enviando respuesta: {response}")


def modificar_matricula(datos):
    ip_camaras = datos['camaras']
    new_plates = datos['new plate'] # Obtengo la matricula nueva
    old_plates = datos['old plate'] # Y la vieja
    ids = obtener_id_matricula(datos) # Obtengo la id de las matriculas a modificar
    for ip_camara in ip_camaras: # Itero sobre los datos obtenidos (Matriculas viejas y nuevas)
        for new_plate in new_plates: 
            for old_plate in old_plates:
                for id in ids:
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
                        consulta = requests.put(
                            f"http://{ip_camara}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",
                            json=json_matricula_actualizada,
                            auth=HTTPDigestAuth(user, passwd),
                            timeout=5
                        )
                        if consulta.status_code == 200:
                            print(f"[SUCCESS] Modificación exitosa para {old_plate} a {new_plate} en {ip_camara}")
                            enviar_respuesta(client_socket, '200 OK', 'Ok')
                            logger.info(f"[SUCCESS] Modificación exitosa para {old_plate} a {new_plate} en {ip_camara}")
                        else:
                            print(f"[ERROR] Fallo al modificar {old_plate} en {ip_camara}: {consulta.status_code}")
                            enviar_respuesta(client_socket, '417 Expectation Failed', f'Error al modificar {old_plate}')
                            logger.error(f"[ERROR] Fallo al modificar {old_plate} en {ip_camara}: {consulta.status_code}")
                    except requests.exceptions.Timeout:
                        print(f"[ERROR] El cliente {ip_camara} demoró en responder")
                        enviar_respuesta(client_socket, '408 Request Timeout', f'Sin respuesta del cliente {ip_camara}')
                        logger.error(f"[ERROR] El cliente {ip_camara} demoró en responder")

def obtener_id_matricula(datos):
    ids = []

    ip_camaras = datos['camaras']

    # Como el cuerpo de la solicitud es diferente cuando se va a modificar la matricula
    # lo adapto para que funcione
    if 'plates' in datos and datos['plates']:
        plates = datos['plates']
    else:
        plates = datos['old plate']
    for ip_camara in ip_camaras:
        for plate in plates:
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
                response = requests.post(url, data=xml, headers=headers, auth=HTTPDigestAuth(user, passwd), timeout=5)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    for elem in root.findall('.//{http://www.hikvision.com/ver20/XMLSchema}id'):
                        ids.append(elem.text)
                    if not ids:
                        print(f"[ERROR] Petición para obtener datos falló: {response.status_code}")
                        logger.warning(f"[ERROR] Petición para obtener datos falló: {response.status_code}")
                else:
                    print(f"[ERROR] Petición para obtener datos falló: {response.status_code}")
                    logger.warning(f"[ERROR] Petición para obtener datos falló: {response.status_code}")
            except requests.exceptions.Timeout:
                print(f"[ERROR] El cliente {ip_camara} demoró en responder")
                logger.error(f"[ERROR] El cliente {ip_camara} demoró en responder") 
    return ids

def borrar_matricula(datos):
    ip_camaras = datos['camaras']
    plates = datos['plates']
    ids = obtener_id_matricula(datos)
    for ip_camara in ip_camaras:
        for plate in plates:
            for id in ids:
                estructura_json = {"id": [id]}
                url = f"http://{ip_camara}/ISAPI/Traffic/channels/1/DelLicensePlateAuditData?format=json"
                try:
                    response = requests.put(url, json=estructura_json, auth=HTTPDigestAuth(user, passwd), timeout=5)
                    if response.status_code == 200:
                        print(f"[DATA DELETED] Dato eliminado: {ip_camara} {plate}")
                        enviar_respuesta(client_socket, '200 OK', 'Ok')
                        logger.info(f"[DATA DELETED] Dato eliminado: {ip_camara} {plate}")
                    else:
                        
                        print(f"[ERROR] Fallo en la petición: {ip_camara} {plate}")
                        enviar_respuesta(client_socket, '204 No Content', 'Matrícula no encontrada')
                        logger.warning(f"[ERROR] Fallo en la petición: {ip_camara} {plate}")
                except requests.exceptions.Timeout:
                    enviar_respuesta(client_socket, '408 Request Timeout', f'Sin respuesta del cliente {ip_camara}')
                    logger.error(f"[ERROR] El cliente {ip_camara} demoró en responder")

def subir_matricula(datos):
    ip_camaras = datos['camaras'] 
    plates = datos['plates']
    for ip_camara in ip_camaras:
        for plate in plates:
            json_matricula_subida = {
                "LicensePlateInfoList": [{
                    "LicensePlate": plate,
                    "listType": "whiteList",
                    "createTime": "",
                    "effectiveStartDate": f"",
                    "effectiveTime": "5000-12-01",
                    "id": ""
                }]
            }
            try:
                consulta = requests.put(
                    f"http://{ip_camara}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",
                    json=json_matricula_subida,
                    auth=HTTPDigestAuth(user, passwd),
                    timeout=5
                )
                if consulta.status_code == 200:
                    print(f"[CLIENT] [DATA UPLOAD] Datos subidos: {ip_camara} {plate}")
                    enviar_respuesta(client_socket, '200 OK', 'Ok')
                    logger.info(f"[CLIENT] [DATA UPLOAD] Datos subidos: {ip_camara} {plate}")
                else:
                    print(f"[CLIENT] [ERROR DATA UPLOAD] Fallo al subir {plate} en {ip_camara}: {consulta.status_code}")
                    enviar_respuesta(client_socket, '417 Expectation Failed', f'Error al subir {plate}')
                    logger.error(f"[CLIENT] [ERROR DATA UPLOAD] Fallo al subir {plate} en {ip_camara}: {consulta.status_code}")
            except requests.exceptions.Timeout:
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
                return data_camaras,action_post
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
        enviar_respuesta(client_socket, '405 Method Not Allowed', 'Método no permitido')
        logger.error("[SERVER] [ERROR] Método no permitido")
    return None

def manejar_solicitud(client_socket):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        logger.info(f"[REQUEST] Solicitud recibida: {request}")
        data,action = obtener_datos(request)
        if data:
            if action == '/AddPlate':
                subir_matricula(data)
            elif action == '/UpdatePlate':
                modificar_matricula(data)
            elif action == '/DeletePlate':
                borrar_matricula(data)
            else:
                print("[ERROR] Operación no reconocida")
                enviar_respuesta(client_socket, '400 Bad Request', 'Operación no reconocida')
                logger.error("[ERROR] Operación no reconocida")
    except Exception as e:
        enviar_respuesta(client_socket, '500 Internal Server Error', 'Error del servidor')
        print("[ERROR] Error del servidor: ", e)
        logger.exception("[ERROR] Error del servidor: ", e)
    finally:
        client_socket.close()

def iniciar_servidor():
    global server_socket,client_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', PUERTO))
    server_socket.listen(5)
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
