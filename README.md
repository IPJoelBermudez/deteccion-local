
## Gestor de Matrículas LPR

Ejecutar el servidor con los argumentos de línea de comandos necesarios:

```sh
python servidor_gestor_matriculas.py -u USUARIO -c CONTRASEÑA [-p PUERTO]
```

- `-u, --usuario`: El usuario para la autenticación HTTP Digest.
- `-c, --contraseña`: La contraseña para la autenticación HTTP Digest.
- `-p, --puerto`: El puerto en el que el servidor escuchará (por defecto: 8080).

**Ejemplo:**

```sh
python servidor_gestor_matriculas.py -u admin -c password -p 8080
```



## Endpoints

### /AddPlate

Añadir una o más matrículas a la lista blanca.

- Método: POST
- Cuerpo de la solicitud: JSON con las IP de las cámaras y las matrículas a agregar.
  ```json
  {
      "camaras":
        [
          "192.168.1.10",
          "192.168.1.11"
        ],
      "plates":
        [
          "ABC123",
          "XYZ789"
        ]
  }
  ```

### /DeletePlate

Eliminar una o más matrículas de la lista blanca.

- Método: POST
- Cuerpo de la solicitud: JSON con las IP de las cámaras y las matrículas a eliminar.
  ```json
  {
      "camaras":
        [
          "192.168.1.10",
          "192.168.1.11"
        ],
      "plates":
        [
          "ABC123",
          "XYZ789"
        ]
  }
  ```
### /UpdatePlate
  Modificar una o más matrículas de la lista blanca.

  - Método: POST
  - Cuerpo de la solicitud: JSON con las IP de las cámaras y las matrículas a modificar.
  ```json
  {
      "camaras":
        [
          "192.168.1.10"
        ],
      "old plate":
        [
          "ABC123",
        ],
      "new plate":
        [
          "ABC124",
        ],
  }
  ```
## Manejo de Señales

El servidor maneja la señal SIGINT (Ctrl+C) para cerrarse limpiamente y liberar el socket.

## Estructura del Código

- `install_dependencies`: Función para instalar las dependencias necesarias.
- `obtener_id_matricula`: Función para obtener las IDs de las matrículas de las cámaras.
- `borrar_matricula`: Función para eliminar matrículas de las cámaras.
- `subir_matricula`: Función para agregar matrículas a las cámaras.
- `obtener_datos`: Función para parsear los datos recibidos en la solicitud HTTP.
- `signal_handler`: Función para manejar la señal SIGINT y cerrar el servidor limpiamente.

## Backup
Para realizar un backup de los datos de matrículas en un dispositivo usando el script que proporcionaste, necesitas ejecutar el script descargar_backup con los siguientes parámetros:

- `-u user:` Nombre de usuario para autenticación en el dispositivo.
- `-p passwd`: Contraseña para autenticación en el dispositivo.
- `-i ip`: Dirección IP del dispositivo.
- `-b backup_path`: Ruta donde se va a guardar el backup.
```sh
python backup_maker.py -u admin -c password -i 192.168.1.10 -b /ruta/backup
```

## Nota

Este script está diseñado para funcionar con cámaras específicas que soportan el protocolo ISAPI de Hikvision. Asegúrese de que sus cámaras sean compatibles y estén configuradas correctamente.


