import os
import sys
import logging
import traceback
import datetime  

# ==============================================
# CONFIGURAZIONE
# ==============================================

# Imposta i percorsi
cartella_script = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cartella_script)

origine = r'C:\dbisam\data'
destinazione = r'C:\dbisam\export'

# Se True, le tabelle con zero record validi vengono comunque esportate (CSV con sola intestazione).
# Se False, vengono saltate.
ESPORTA_TABELLE_VUOTE = False

# ==============================================
# INIZIO SCRIPT
# ==============================================

if not os.path.exists(destinazione):
    os.makedirs(destinazione)

log_path = os.path.join(cartella_script, 'esportazione.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def estrai_nomi_campi_binari(file_path):
    """Funzione di fallback per leggere i nomi dei campi dal file binario."""
    nomi = []
    try:
        with open(file_path, 'rb') as f:
            header = f.read(2048)
            current_name = []
            for byte in header:
                if 32 <= byte <= 126:
                    current_name.append(chr(byte))
                else:
                    if len(current_name) > 1:
                        name_str = "".join(current_name)
                        if name_str.isidentifier() and name_str.upper() not in ('DBISAM', 'TABLE', 'INDEX'):
                            nomi.append(name_str)
                    current_name = []
    except Exception:
        pass
    return nomi

# ---- Import ----
try:
    from pydbisam import PyDBISAM
except Exception as e:
    logging.critical(f"Impossibile importare pydbisam: {e}")
    input("Premi Invio per uscire...")
    sys.exit(1)

# ---- Verifica cartella origine ----
if not os.path.exists(origine):
    logging.error(f"La cartella di origine '{origine}' non esiste.")
    input("Premi Invio per uscire...")
    sys.exit(1)

files_dat = [f for f in os.listdir(origine) if f.lower().endswith('.dat')]
if not files_dat:
    logging.warning(f"Nessun file .dat trovato in '{origine}'.")
    input("Premi Invio per uscire...")
    sys.exit(0)

logging.info("=== INIZIO PROCESSO DI ESPORTAZIONE ===")

for filename in files_dat:
    file_path = os.path.join(origine, filename)
    csv_name = filename.replace('.dat', '.csv')
    csv_path = os.path.join(destinazione, csv_name)

    logging.info(f"Elaborazione di {filename}...")

    try:
        with PyDBISAM(file_path) as db:
            # Controllo tabelle vuote
            if not ESPORTA_TABELLE_VUOTE and db.total_rows == 0:
                logging.info(f"  Tabella '{filename}' vuota (total_rows=0), saltata.")
                continue

            # Raccoglie le colonne esportabili
            export_columns = [col for col in db._columns if col.is_exportable]
            if not export_columns:
                logging.warning(f"  Nessuna colonna esportabile, tabella saltata.")
                continue

            headers = [col.name for col in export_columns]
            export_indices = [col.index - 1 for col in export_columns]  # 0-based

            # Logga i campi esclusi e quelli sconosciuti
            for col in db._columns:
                if not col.is_exportable:
                    logging.info(f"  Campo escluso: '{col.name}' (tipo: {col.type})")
                if col.is_unknown_type:
                    logging.warning(f"  Campo sconosciuto: '{col.name}' (typeid={col.type._value_}) – esportato vuoto")

            # Scrittura CSV
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(",".join(headers) + "\n")

                row_count = 0
                for row in db.rows():
                    valori = []
                    for idx in export_indices:
                        val = row[idx]
                        # Formatta le date nel formato italiano (opzionale)
                        if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
                            val = val.strftime('%d/%m/%Y')
                        elif isinstance(val, datetime.time):
                            val = val.strftime('%H:%M:%S')
                        else:
                            val = '' if val is None else str(val)
                        valori.append(val)
                    f.write(",".join(valori) + "\n")
                    row_count += 1

            logging.info(f"  Completato: {csv_name} ({row_count} righe)")

    except Exception as e:
        logging.error(f"ERRORE su {filename}: {e}")
        logging.debug(traceback.format_exc())
        # Tentativo di recupero nomi colonne
        nomi = estrai_nomi_campi_binari(file_path)
        logging.error(f"  Campi rilevati: {nomi}")

logging.info("=== PROCESSO DI ESPORTAZIONE TERMINATO ===")
input("Premi Invio per uscire...")
