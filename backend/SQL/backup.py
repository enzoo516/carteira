# SQL/backup.py
import shutil
import os
from datetime import datetime

def fazer_backup():
    if not os.path.exists("data/ativos.db"):
        return
        
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/ativos_{timestamp}.db"
    shutil.copy2("data/ativos.db", backup_file)