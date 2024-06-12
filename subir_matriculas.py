import socket
import requests
from requests.auth import HTTPDigestAuth 
import json
import argparse


def subir_datos(datos):
  
    ip_camaras = datos['camaras']
    plates     = datos['plates']
    for ip_camara in ip_camaras:
        for plate in plates:
            json_matricula_subida = {
            "LicensePlateInfoList": [{
                "LicensePlate": f"{plate}",
                "listType": "whiteList",
                "createTime": "2024-03-26T16:30:34",
                "effectiveStartDate": "2024-03-26",
                "effectiveTime": "3000-12-01",
                "id": ""
                }]
            }
            consulta = requests.put(f"http://{ip_camara}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",json=json_matricula_subida,auth=HTTPDigestAuth(user,passwd))
            print(consulta.status_code)

    return NotImplementedError("Por implementar")


def obtener_datos(request):
    # Formateo los headers, separando todo en una lista
    headers = request.split('\r\n')

    # Busco cuando termine en POST
    if headers[0].startswith('POST'):
        # Buscar la línea en blanco que indica el final de los headers
        idx = request.find('\r\n\r\n')
        if idx != -1:
            body = request[idx + 4:]  # El cuerpo de la solicitud empieza después de la línea en blanco
            data_camaras = json.loads(body)  # Parsear el JSON
            return data_camaras 
        else:
            response = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nCuerpo de solicitud no encontrado'
            client_socket.sendall(response.encode())
    else:
        response = 'HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/plain\r\n\r\nMétodo no permitido'
        client_socket.sendall(response.encode())

if __name__ == "__main__":
    global user
    global passwd
    global puerto

    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Servidor HTTP')
    parser.add_argument('-u', '--usuario', required=True, help='Usuario')
    parser.add_argument('-c', '--contraseña', required=True, help='Contraseña')
    parser.add_argument('-p', '--puerto', type=int, default=8080, help='Puerto del servidor (por defecto: 8080)')
    args = parser.parse_args()

    # Obtener usuario, contraseña y puerto
    user = args.usuario
    passwd = args.contraseña
    puerto = args.puerto

    # Configuración del servidor
    HOST = socket.getfqdn()
    IP_LOCAL = socket.gethostbyname_ex(HOST)[2][1]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((IP_LOCAL, puerto))
        server_socket.listen()

        print(f"Servidor escuchando en {IP_LOCAL}:{puerto}")

        while True:
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print(f"Conexión establecida con {client_address}")
                request = client_socket.recv(2048).decode()
                print(request)
                # Consulto que tipo de accion se va a realizar
                if request.split(" ")[1] == "/DeletePlate":
                    response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nEliminar'

                elif request.split(" ")[1] == "/AddPlate":
                    subir_datos(obtener_datos(request))
                    response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nDatos agregados'
                else:
                    response = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nCuerpo de solicitud no encontrado'
                
                # Envio la respuesta
                client_socket.sendall(response.encode())
                break