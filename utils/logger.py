from .modules import datetime,log,RotatingFileHandler,os

def setup_logger(log_filename=f'{datetime.now().strftime("%Y-%m-%d")}.log'):
    '''
    Descripción: Esta función configura y devuelve un objeto logger que permite el registro
    de mensajes con diferentes niveles de severidad, como debug, info, warning, error y critical.
    Estos mensajes son útiles para el seguimiento y depuración del comportamiento de la aplicación.

    Los archivos de log se guardan en una carpeta 'Logs', con nombres que incluyen la fecha actual,
    facilitando la organización y el seguimiento temporal de los eventos registrados.

    Parámetros:
        No acepta parámetros.

    Retorna:
        logger (logging.Logger): Un objeto logger configurado para escribir en un archivo con rotación.
    '''

    # Crea la carpeta 'Logs' si no existe
    log_directory = "Logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    

    # Crea un logger
    logger = log.getLogger("MyLogger")
    logger.setLevel(log.DEBUG)  # Puedes cambiar esto a INFO, WARNING, etc.

    # Crea un handler para escribir los logs en un archivo con la fecha actual en el nombre
    log_path = os.path.join(log_directory, log_filename)
    handler = RotatingFileHandler(log_path, maxBytes=10000, backupCount=5)
    handler.setLevel(log.DEBUG)

    # Define el formato del log
    formatter = log.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d : %H:%M:%S')
    handler.setFormatter(formatter)

    # Añade el handler al logger
    logger.addHandler(handler)
    return logger

# Configura el logger
logger = setup_logger()


