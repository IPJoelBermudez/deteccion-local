from .modules import argparse,time,schedule
from tools import descargar_backup, subir_backup

def job(user, passwd, ip, path_backup):
    descargar_backup(user, passwd, ip)
    #subir_backup(ip, user, passwd, path_backup)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup maker script")
    parser.add_argument("-u", "--user", type=str, required=True, help="Username for authentication")
    parser.add_argument("-p", "--passwd", type=str, required=True, help="Password for authentication")
    parser.add_argument("-i", "--ip", type=str, required=True, help="IP address of the device")
    parser.add_argument("-b", "--path_backup", type=str, required=True, help="Path to the backup file")
    
    args = parser.parse_args()

    schedule.every().hour.do(job, args.user, args.passwd, args.ip, args.path_backup)
    
    print("Backup maker corriendo. Ctrl+C para salir.")
    while True:
        schedule.run_pending()
        time.sleep(1)
