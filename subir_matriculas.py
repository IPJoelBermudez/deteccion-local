import socket
import requests
from requests.auth import HTTPDigestAuth
import json
import argparse

def borrar_matricula(datos):
    return NotImplementedError

def subir_matricula(datos):
    ip_camaras = datos['camaras']
    plates = datos['plates']
    
    for ip_camara in ip_camaras:
        for plate in plates:
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
            consulta = requests.put(
                f"http://{ip_camara}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",
                json=json_matricula_subida,
                auth=HTTPDigestAuth(user, passwd)
            )
            
            if consulta.status_code == 200:
                response = f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nAgregando {plate}\r'
                print(f"[SUCCESS] Subida exitosa para {plate} en {ip_camara}")
            else:
                response = f'HTTP/1.1 417 Expectation Failed\r\nContent-Type: text/plain\r\n\r\nError al subir {plate}'
                print(f"[ERROR] Fallo al subir {plate} en {ip_camara}: {consulta.status_code}")
            
            client_socket.sendall(response.encode())
            print(f"[RESPONSE] Enviando respuesta al cliente: {response}")

    return NotImplementedError("Por implementar")

def obtener_datos(request):
    headers = request.split('\r\n')
    
    if headers[0].startswith('POST'):
        idx = request.find('\r\n\r\n')
        if idx != -1:
            body = request[idx + 4:]
            data_camaras = json.loads(body)
            print(f"[DATA RECEIVED] Datos recibidos: {data_camaras}")
            return data_camaras
        else:
            response = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\rCuerpo de solicitud no encontrado'
            client_socket.sendall(response.encode())
            print("[ERROR] Cuerpo de solicitud no encontrado")
    else:
        response = 'HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/plain\rMétodo no permitido'
        client_socket.sendall(response.encode())
        print("[ERROR] Método no permitido")

if __name__ == "__main__":
    global user
    global passwd
    global puerto

    parser = argparse.ArgumentParser(description='Servidor HTTP')
    parser.add_argument('-u', '--usuario', required=True, help='Usuario')
    parser.add_argument('-c', '--contraseña', required=True, help='Contraseña')
    parser.add_argument('-p', '--puerto', type=int, default=8080, help='Puerto del servidor (por defecto: 8080)')
    args = parser.parse_args()

    user = args.usuario
    passwd = args.contraseña
    puerto = args.puerto

    HOST = socket.getfqdn()
    IP_LOCAL = socket.gethostbyname_ex(HOST)[2][1]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((IP_LOCAL, puerto))
        server_socket.listen()

        print(f"[SERVER STARTED] Servidor escuchando en {IP_LOCAL}:{puerto}")
        
        while True:
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print(f"[CONNECTION] Conexión establecida con: {client_address}")

                request = client_socket.recv(2048).decode()
                print(f"[REQUEST RECEIVED] [{client_address}] Contenido: {request}")

                if request.split(" ")[1] == "/DeletePlate":
                    response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nEliminar'
                    client_socket.sendall(response.encode())
                    print("[RESPONSE] Enviando respuesta: Eliminar")
                
                elif request.split(" ")[1] == "/AddPlate":
                    datos = obtener_datos(request)
                    if datos:
                        subir_datos(datos)
                
                else:
                    response = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\rCuerpo de solicitud no encontrado'
                    client_socket.sendall(response.encode())
                    print("[ERROR] Cuerpo de solicitud no encontrado")
                    
                print("[CLOSE CONNECTION] Conexión cerrada con el cliente")
                break
