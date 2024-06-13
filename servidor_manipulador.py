import socket
import subprocess
import requests

# Lista de dependencias
dependencies = ["requests"]

# Función para instalar las dependencias usando pip
def install_dependencies(packages):
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"[INSTALLING] Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Instalar las dependencias
install_dependencies(dependencies)
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
import json
import argparse
import time
import signal
import sys

# Variables globales para el usuario, la contraseña y el puerto
global user
global passwd
global PUERTO
global server_socket

def obtener_id_matricula(datos):
    ids = []

    ip_camaras = datos['camaras']
    plates = datos['plates']

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

            response = requests.post(url, data=xml, headers=headers, auth=HTTPDigestAuth(user, passwd))
            
            if response.status_code == 200:
                print("[SUCCESS] Petición enviada exitosamente")
            else:
                print(f"[ERROR] Fallo en la petición: {response.status_code}")
                continue  # Salta a la siguiente iteración si hay un error en la solicitud
            
            # Parsear el contenido XML de la respuesta
            root = ET.fromstring(response.content)
            for elem in root.findall('.//{http://www.hikvision.com/ver20/XMLSchema}id'):
                ids.append(elem.text)
    
    return ids

def borrar_matricula(datos):
    ip_camaras = datos['camaras']
    ids = obtener_id_matricula(datos)
    for ip_camara in ip_camaras:
        for id in ids:
            estrucutra_json = {"id":[f"{id}"]}
            url = f"http://{ip_camara}/ISAPI/Traffic/channels/1/DelLicensePlateAuditData?format=json"
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, json=estrucutra_json, headers=headers, auth=HTTPDigestAuth(user, passwd))
            if response.status_code == 200:
                response = f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nMatricula eliminada \r'
                print("[SUCCESS] Petición enviada exitosamente")
            else:
                response = f'HTTP/1.1 204 No Content\r\nContent-Type: text/plain\r\n\r\nMatricula no encontrada \r'
                print(f"[ERROR] Fallo en la petición: {response.status_code}")
                continue  # Salta a la siguiente iteración si hay un error en la solicitud
            client_socket.sendall(response.encode())

    return True

def subir_matricula(datos):
    # Obtengo las IP de las cámaras y las matrículas
    ip_camaras = datos['camaras']
    plates = datos['plates']
    
    for ip_camara in ip_camaras:
        for plate in plates:
            # Creo el JSON con la información de la matrícula
            json_matricula_subida = {
                "LicensePlateInfoList": [{
                    "LicensePlate": f"{plate}",
                    "listType": "whiteList",
                    "createTime": "2024-03-26T16:30:34",
                    "effectiveStartDate": "2024-03-26",
                    "effectiveTime": "5000-12-01", 
                    "id": ""
                }]
            }
            # Hago la solicitud PUT para subir la matrícula
            consulta = requests.put(
                f"http://{ip_camara}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",
                json=json_matricula_subida,
                auth=HTTPDigestAuth(user, passwd)
            )
            
            # Manejo las respuestas de la solicitud
            if consulta.status_code == 200:
                response = f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nAgregando {plate}\r'
                print(f"[SUCCESS] Subida exitosa para {plate} en {ip_camara}")
            else:
                response = f'HTTP/1.1 417 Expectation Failed\r\nContent-Type: text/plain\r\n\r\nError al subir {plate}'
                print(f"[ERROR] Fallo al subir {plate} en {ip_camara}: {consulta.status_code}")
            
            # Envío la respuesta al cliente
            client_socket.sendall(response.encode())
            print(f"[RESPONSE] Enviando respuesta al cliente: {response}")

    return NotImplementedError("Por implementar")

def obtener_datos(request):
    # Separar los headers en una lista
    headers = request.split('\r\n')
    
    # Verificar si el método es POST
    if headers[0].startswith('POST'):
        # Buscar el índice de la línea en blanco que separa los headers del cuerpo
        idx = request.find('\r\n\r\n')
        if idx != -1:
            body = request[idx + 4:]  # Obtener el cuerpo de la solicitud
            data_camaras = json.loads(body)  # Parsear el JSON
            print(f"[DATA RECEIVED] Datos recibidos: {data_camaras}")
            return data_camaras
        else:
            response = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nCuerpo de solicitud no encontrado'
            client_socket.sendall(response.encode())
            print("[ERROR] Cuerpo de solicitud no encontrado")
    else:
        response = 'HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/plain\r\n\r\nMétodo no permitido'
        client_socket.sendall(response.encode())
        print("[ERROR] Método no permitido")

def signal_handler(sig, frame):
    print("\n[SHUTDOWN] Cerrando el servidor...")
    if server_socket:
        server_socket.close()
    sys.exit(0)

if __name__ == "__main__":
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Servidor HTTP')
    parser.add_argument('-u', '--usuario', required=True, help='Usuario')
    parser.add_argument('-c', '--contraseña', required=True, help='Contraseña')
    parser.add_argument('-p', '--puerto', type=int, default=8080, help='Puerto del servidor (por defecto: 8080)')
    args = parser.parse_args()

    # Asignar los valores de usuario, contraseña y puerto
    user = args.usuario
    passwd = args.contraseña
    PUERTO = args.puerto

    # Obtener el nombre de host y la IP local
    HOST = socket.getfqdn()
    IP_LOCAL = socket.gethostbyname_ex(HOST)[2][1]

    # Configurar el manejador de señal para `Ctrl+C`
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((IP_LOCAL, PUERTO))
            server_socket.listen(5)
            print(f"[SERVER STARTED] Servidor escuchando en {IP_LOCAL}:{PUERTO}")
            
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    with client_socket:
                        print(f"[CONNECTION] Conexión establecida con: {client_address}")

                        # Recibir la solicitud del cliente
                        request = client_socket.recv(2048).decode()
                        print(f"[REQUEST RECEIVED] [{client_address}] Contenido: {request}")

                        # Determinar la acción a realizar según la solicitud
                        if request.split(" ")[1] == "/DeletePlate":
                            datos = obtener_datos(request)
                            borrar_matricula(datos)
                        elif request.split(" ")[1] == "/AddPlate":
                            datos = obtener_datos(request)
                            if datos:
                                subir_matricula(datos)
                        else:
                            response = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nCuerpo de solicitud no encontrado'
                            client_socket.sendall(response.encode())
                            print("[ERROR] Cuerpo de solicitud no encontrado")
                
                except Exception as e:
                    print(f"[ERROR] Error en la comunicación con el cliente: {e}")
                    continue  # Continuar con el siguiente cliente en caso de error

        except Exception as e:
            print(f"[ERROR] Error en el servidor: {e}")
            print("[RESTART] Reiniciando el servidor en 5 segundos...")
            time.sleep(5)  # Esperar 5 segundos antes de intentar reiniciar el servidor
