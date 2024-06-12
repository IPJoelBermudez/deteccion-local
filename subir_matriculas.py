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




def obtener_datos(request):
    headers = request.split('\r\n')
    if headers[0].startswith('POST'):
        data_lpr =  " ".join(headers[headers.index('{'):-1])
        data_lpr = json.loads(data_lpr.replace(' ','') + '}')
        
        print(data_lpr)
        print(data_lpr)
        # Enviar una respuesta al cliente
        response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nPetición POST recibida'
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
                request = client_socket.recv(1024).decode()
                obtener_datos(request)
                response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nJoya'
                client_socket.sendall(response.encode())
                break
                