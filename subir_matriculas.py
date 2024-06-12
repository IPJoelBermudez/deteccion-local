import socket
import json

estrucutraJson = {
    "LicensePlateInfoList": [{
        "LicensePlate": "BBB1234",
        "listType": "whiteList",
        "createTime": "2024-03-26T16:30:34",
        "effectiveStartDate": "2024-03-26",
        "effectiveTime": "2024-03-26",
        "id": ""
    }]
}

def subir_datos(data_camaras):
    pass

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
            print(data_camaras)
            return data_camaras 
        else:
            response = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nCuerpo de solicitud no encontrado'
            client_socket.sendall(response.encode())
    else:
        response = 'HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/plain\r\n\r\nMétodo no permitido'
        client_socket.sendall(response.encode())

if __name__ == "__main__":
    # Configuración del servidor
    HOST = socket.getfqdn() # Dirección IP del servidor (localhost)
    IP_LOCAL =  socket.gethostbyname_ex(HOST)[2][1]
    PORT = 8080         # Puerto del servidor
    # Crear un socket TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((IP_LOCAL, PORT))  # Vincular el socket a la dirección y puerto
        server_socket.listen()            # Poner el socket en modo de escucha

        print(f"Servidor escuchando en {IP_LOCAL}:{PORT}")

        while True:
            # Esperar a que un cliente se conecte
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print(f"Conexión establecida con {client_address}")
                request = client_socket.recv(2048).decode()
                obtener_datos(request)
                #obtener_datos(request)
                response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nJoya'
                client_socket.sendall(response.encode())
                break
                