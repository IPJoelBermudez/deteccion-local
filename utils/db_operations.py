from .modules import random,mysql

# Verifica si una estadía ya existe en la base de datos
def existe_estadia(cursor, Creation_day, vehicle_id):
    Creation_day = Creation_day[:16]  # Recorta la fecha para tener precisión hasta los minutos
    cursor.execute(f"select id from stay_new_kit where DateJoin like '{Creation_day}%' and vehicle = '{vehicle_id}'")
    existe = cursor.fetchone()
    return bool(existe)  # Devuelve True si la estadía existe, False en caso contrario

# Genera un código aleatorio
def generar_codigo_random():
    return random.randrange(10000000000000, 100000000000000)

# Obtiene el ID del estacionamiento basado en el DNS
def obtener_id_parking(dns, cursor):
    cursor.execute("select parking from gate where url = %s", (dns,))
    return cursor.fetchone()[0]

# Obtiene el ID del usuario basado en la matrícula del vehículo
def obtener_id_usuario(plate, cursor):
    try:
        cursor.execute("select user from vehicle_new_kit where plate = %s", (plate,))
        id = cursor.fetchone()
        return id[0] if id else None  # Devuelve el ID del usuario o None si no se encuentra
    except mysql.connector.Error as err:
        return None

# Obtiene el ID del vehículo basado en la matrícula y el ID del usuario
def obtener_id_vehicle(cursor, plate, user):
    cursor.execute("select id from vehicle_new_kit where plate = %s and user = %s", (plate, user))
    return cursor.fetchone()[0]

# Obtiene el estado de empleado basado en el ID del usuario
def obtener_status_employee(cursor, user_id):
    cursor.execute("select employee from user_new_kit where id = %s", (user_id,))
    return cursor.fetchone()[0]

# Obtiene el ID de la puerta basado en la URL del LPR
def obtener_id_gate(cursor,lpr_url):
    try:
        cursor.execute("select id from gate where url = %s", (lpr_url,))
        return cursor.fetchone()[0]
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Crea un nuevo ID de tarifa en la base de datos
def crear_id_rate(cursor,conn,Date):
    try:
        # Consulta de inserción
        query = """
        INSERT INTO `rate` 
        (`startDate`, `endDate`, `cost`, `CreationDay`, `active`, `type`) 
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        # Valores a insertar
        values = (Date, None, 0, Date, 1, 'stay')
        
        # Ejecución de la consulta
        cursor.execute(query, values)
        conn.commit()
        
        # Obtener el último ID insertado
        last_id = cursor.lastrowid
        return last_id
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    


# Crea un nuevo ID de ítem en la base de datos
def crear_id_item(conn,cursor,barcode, id_rate, CreationDay):
    try:
        # Consulta de inserción
        query = """
        INSERT INTO `item` 
        (`rate`, `code`, `CreationDay`, `Active`, `type`) 
        VALUES (%s, %s, %s, %s, %s);
        """
        
        # Valores a insertar
        values = (id_rate, barcode, CreationDay, 1, 'stay')
        
        # Ejecución de la consulta
        cursor.execute(query, values)
        conn.commit()
        
        # Obtener el último ID insertado
        last_id = cursor.lastrowid
        return last_id
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
  
# Inserta una nueva estadía en la base de datos
def agregar_estadia(conn,cursor,id, user, employee, vehicle, income, parking, gate_in, gate_out, DateJoin, DateLeave, enabled, manual, amount, barcode, alphanumericcode, url_lpr_in, url_lpr_out):
    try:
        # Consulta de inserción
        query = """
        INSERT INTO `stay_new_kit` 
        (`id`,`user`,`employee`, `vehicle`, `income`, `parking`, `gate_in`, `gate_out`, `DateJoin`, `DateLeave`, `enabled`, `manual`, `amount`, `barcode`, `alphanumericcode`, `url_lpr_in`, `url_lpr_out`) 
        VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        # Valores a insertar
        values = (id, user, employee, vehicle, income, parking, gate_in, gate_out, DateJoin, DateLeave, enabled, manual, amount, barcode, alphanumericcode, url_lpr_in, url_lpr_out)
        
        # Ejecución de la consulta
        cursor.execute(query, values)
        conn.commit()
        print("Datos insertados correctamente.")
        last_id = int(cursor.lastrowid)
        return last_id
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")

def cerrar_estadia(cursor,conn,id_stay,id_vehicle,date_in,DateLeave):
    try:
        query = f"UPDATE stay_new_kit SET DateLeave = '{DateLeave}' WHERE vehicle = '{id_vehicle}' AND DateJoin = '{date_in}' AND id = '{id_stay}'"
        print(query)
        cursor.execute(query)

        conn.commit()
        print("Estadia cerrada correctamente.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
