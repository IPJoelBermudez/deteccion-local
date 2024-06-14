import os
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime
import pandas as pd
from logger import logger

def descargar_backup(user, passwd, ip):
    path = "./backup/"
    # Crear la carpeta si no existe
    os.makedirs(path, exist_ok=True)
    
    url = f"http://{ip}/ISAPI/Traffic/channels/1/licensePlateAuditData?fileType=csv"
    
    response = requests.get(url, auth=HTTPDigestAuth(user, passwd))
    
    if response.status_code == 200:
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = path + f"license_plate_data_{fecha_actual}.csv"
        with open(nombre_archivo, "wb") as file:
            file.write(response.content)
        print(f"[SUCCESS] Archivo CSV descargado exitosamente: {nombre_archivo}")
        logger.info(f"[SUCCESS BACKUP] Archivo CSV descargado exitosamente: {nombre_archivo}")

    else:
        print(f"[ERROR] Fallo en la petición: {response.status_code}")
        logger.critical(f"[ERROR] Fallo en la petición: {response.status_code}")


def subir_backup(ip, user, passwd, path_backup):
    # Leer el archivo CSV
    csv_file = path_backup
    df = pd.read_csv(csv_file)
    
    # Obtener la fecha y hora actual en el formato deseado
    create_time = datetime.now().isoformat(timespec='seconds')  

    # Iterar sobre cada fila del CSV
    for _, row in df.iterrows():
        id = row['No.']
        plate = row['Plate No.']
        list_type = 'whiteList' if row['Group(0 BlockList, 1 AllowList)'] == 1 else 'blockList'
        effective_start_date = row['Effective Start Date (Format: YYYY-MM-DD, e.g., 2017-12-07)']
        effective_end_date = row['Effective End Date (Format: YYYY-MM-DD, e.g., 2017-12-07)']
        
        # Crear el JSON con la información de la matrícula
        json_matricula_subida = {
            "LicensePlateInfoList": [
                {
                    "LicensePlate": f"{plate}",
                    "listType": f"{list_type}",
                    "createTime": f"{create_time}", 
                    "effectiveStartDate": f"{effective_start_date}",
                    "effectiveTime": f"{effective_end_date}",
                    "id": f"{id}"  
                }
            ]
        }
        
        # Hacer la solicitud PUT para subir la matrícula
        consulta = requests.put(
            f"http://{ip}/ISAPI/Traffic/channels/1/licensePlateAuditData/record?format=json",
            json=json_matricula_subida,
            auth=HTTPDigestAuth(user, passwd)
        )
        
        # Manejo de las respuestas de la solicitud
        if consulta.status_code == 200:
            print(f"[SUCCESS] Subida exitosa para {plate} en {ip}")
            logger.info(f"[SUCCESS] Subida exitosa para {plate} en {ip}")

            
        else:
            print(f"[ERROR] Fallo al subir {plate} en {ip}: {consulta.status_code}")
            logger.critical(f"[ERROR] Fallo al subir {plate} en {ip}: {consulta.status_code}")
