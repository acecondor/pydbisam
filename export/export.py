# Copyright (c) 2026, Maurizio Condini <maurizio@defcon.it>

import os
import sys
import csv
import logging
import traceback
import datetime

# ==============================================
# CONFIGURAZIONE
# ==============================================

cartella_script = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cartella_script)

origine = r'C:\dbisam\data'
destinazione = r'C:\dbisam\export'

# Se True, le tabelle con zero record validi vengono comunque esportate (CSV con sola intestazione).
# Se False, vengono saltate.
ESPORTA_TABELLE_VUOTE = False

# -- OPZIONI SCHEMA.INI --
# Se True, crea UN SOLO file Schema.ini per l'intera cartella di destinazione (standard Access).
CREA_SCHEMA_INI_UNICO = True
# Se True, crea UN file Schema.ini per OGNI CSV esportato (es. TABELLA.csv -> TABELLA.ini).
CREA_SCHEMA_INI_SINGOLO = False
# Nota: le due opzioni possono coesistere; se entrambe False, non viene creato alcun Schema.ini.

# -- PULIZIA CARTELLA DI DESTINAZIONE --
# Se True, cancella TUTTI i file .csv e .ini presenti nella cartella di destinazione
# prima di iniziare l'esportazione.
CANCELLA_FILE_ESPORTATI = True

# Separatore di campo per il CSV (',' per virgola, ';' per punto e virgola, '\t' per tab)
SEPARATORE_CSV = ','

# Qualificatore di testo per i campi che contengono il separatore o a capo.
# Valori comuni: '"' (doppio apice) o "'" (apice singolo). Impostare a '' per nessuno.
QUALIFICATORE_TESTO = '"'

# ==============================================
# NOTE SU SCHEMA.INI
# ==============================================
# Schema.ini è un file di configurazione usato dal motore Jet/ACE di Microsoft Access
# (e da altre applicazioni che usano il driver "Text" ODBC) per interpretare
# i file CSV. Deve avere lo stesso nome del file CSV ma estensione .ini
# (es. TABELLA.csv -> TABELLA.ini) e risiedere nella stessa cartella.
#
# Opzioni principali di Schema.ini:
#   - Format=CSVDelimited       (oppure Delimited(;) per punto e virgola)
#   - Delimiter=,               (carattere separatore)
#   - MaxScanRows=0             (0 = esamina tutte le righe per determinare il tipo)
#   - CharacterSet=ANSI         (oppure OEM, UTF-8, UTF-16)
#   - TextDelimiter="           (qualificatore testo; default ")
#   - DateTimeFormat=           (formato data/ora; se omesso usa le impostazioni di sistema)
#   - DecimalSymbol=.           (separatore decimale; default .)
#   - NumberDigits=4            (numero di decimali per i campi Double)
#   - ColNameHeader=True        (prima riga = intestazione colonne)
#
# Tipi di dati per colonna:
#   ColN=NomeCampo Tipo [Larghezza]
#   Tipi validi: Bit, Byte, Short, Long, Currency, Single, Double, DateTime, Char, Memo
# ==============================================

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

def scrivi_sezione_schema_ini(file_handle, csv_filename, export_columns):
    """
    Scrive una sezione [NomeFile.csv] nel file Schema.ini aperto.
    """
    file_handle.write(f"[{csv_filename}]\n")
    file_handle.write("Format=CSVDelimited\n")
    file_handle.write(f"Delimiter={SEPARATORE_CSV}\n")
    file_handle.write("MaxScanRows=0\n")
    file_handle.write("CharacterSet=ANSI\n")
    file_handle.write("ColNameHeader=True\n")
    file_handle.write("DateTimeFormat=yyyy-MM-dd HH:mm:ss\n")
    if QUALIFICATORE_TESTO:
        file_handle.write(f"TextDelimiter={QUALIFICATORE_TESTO}\n")
    file_handle.write("\n")

    for idx, col in enumerate(export_columns, start=1):
        ftype = col.type
        nome = col.name.replace(' ', '_')
        if ftype in (FieldType.STRING, FieldType.FIXEDCHAR):
            width = max(col.size, 255)
            if width > 255:
                file_handle.write(f"Col{idx}={nome} Memo\n")
            else:
                file_handle.write(f"Col{idx}={nome} Char Width {width}\n")
        elif ftype == FieldType.BOOLEAN:
            file_handle.write(f"Col{idx}={nome} Bit\n")
        elif ftype in (FieldType.DATE, FieldType.TIME, FieldType.TIMESTAMP):
            file_handle.write(f"Col{idx}={nome} DateTime\n")
        elif ftype == FieldType.SHORT_INTEGER:
            file_handle.write(f"Col{idx}={nome} Short\n")
        elif ftype in (FieldType.INTEGER, FieldType.AUTOINCREMET, FieldType.AUTOINC_LARGE):
            file_handle.write(f"Col{idx}={nome} Long\n")
        elif ftype in (FieldType.CURRENCY, FieldType.BCD):
            file_handle.write(f"Col{idx}={nome} Currency\n")
        elif ftype == FieldType.FLOAT:
            file_handle.write(f"Col{idx}={nome} Double\n")
        else:
            file_handle.write(f"Col{idx}={nome} Char Width 255\n")

    file_handle.write("\n")

def cancella_vecchi_export():
    """
    Elimina tutti i file .csv e .ini presenti nella cartella di destinazione.
    """
    if not os.path.exists(destinazione):
        return
    for file in os.listdir(destinazione):
        if file.lower().endswith(('.csv', '.ini')):
            os.remove(os.path.join(destinazione, file))
            logging.info(f"  Rimosso vecchio file: {file}")

try:
    from pydbisam import PyDBISAM
    from pydbisam.field import FieldType
except Exception as e:
    logging.critical(f"Impossibile importare pydbisam: {e}")
    input("Premi Invio per uscire...")
    sys.exit(1)

if not os.path.exists(origine):
    logging.error(f"La cartella di origine '{origine}' non esiste.")
    input("Premi Invio per uscire...")
    sys.exit(1)

files_dat = [f for f in os.listdir(origine) if f.lower().endswith('.dat')]
if not files_dat:
    logging.warning(f"Nessun file .dat trovato in '{origine}'.")
    input("Premi Invio per uscire...")
    sys.exit(0)

# -- Cancellazione preliminare --
if CANCELLA_FILE_ESPORTATI:
    logging.info("Pulizia cartella di destinazione...")
    cancella_vecchi_export()

# -- Preparazione Schema.ini unico (se richiesto) --
schema_unico_path = os.path.join(destinazione, 'Schema.ini')
if CREA_SCHEMA_INI_UNICO:
    # Cancella eventuale Schema.ini preesistente e crea uno nuovo vuoto
    if os.path.exists(schema_unico_path):
        os.remove(schema_unico_path)
    # Il file verrà scritto man mano nel ciclo (modalità append)

logging.info("=== INIZIO PROCESSO DI ESPORTAZIONE ===")

for filename in files_dat:
    file_path = os.path.join(origine, filename)
    csv_name = filename.replace('.dat', '.csv')
    csv_path = os.path.join(destinazione, csv_name)

    logging.info(f"Elaborazione di {filename}...")

    try:
        with PyDBISAM(file_path) as db:
            if not ESPORTA_TABELLE_VUOTE and db.total_rows == 0:
                logging.info(f"  Tabella '{filename}' vuota (total_rows=0), saltata.")
                continue

            export_columns = [col for col in db._columns if col.is_exportable]
            if not export_columns:
                logging.warning(f"  Nessuna colonna esportabile, tabella saltata.")
                continue

            headers = [col.name for col in export_columns]
            export_indices = [col.index - 1 for col in export_columns]

            for col in db._columns:
                if not col.is_exportable:
                    logging.info(f"  Campo escluso: '{col.name}' (tipo: {col.type})")
                if col.is_unknown_type:
                    logging.warning(f"  Campo sconosciuto: '{col.name}' (typeid={col.type._value_}) – esportato vuoto")

            # Scrittura CSV
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(
                    f,
                    delimiter=SEPARATORE_CSV,
                    quotechar=QUALIFICATORE_TESTO if QUALIFICATORE_TESTO else '"',
                    quoting=csv.QUOTE_NONNUMERIC if QUALIFICATORE_TESTO else csv.QUOTE_NONE,
                    escapechar='\\' if QUALIFICATORE_TESTO else None
                )
                writer.writerow(headers)
                row_count = 0
                for row in db.rows():
                    valori = []
                    for idx in export_indices:
                        val = row[idx]
                        if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
                            val = val.strftime('%Y-%m-%d')
                        elif isinstance(val, datetime.time):
                            val = val.strftime('%H:%M:%S')
                        elif isinstance(val, datetime.datetime):
                            val = val.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            val = '' if val is None else str(val)
                        valori.append(val)
                    writer.writerow(valori)
                    row_count += 1

            logging.info(f"  Completato: {csv_name} ({row_count} righe)")

            # -- Schema.ini per singolo CSV --
            if CREA_SCHEMA_INI_SINGOLO:
                schema_singolo_path = csv_path.replace('.csv', '.ini')
                with open(schema_singolo_path, 'w', encoding='utf-8') as sf:
                    scrivi_sezione_schema_ini(sf, csv_name, export_columns)
                logging.info(f"  Creato Schema.ini: {schema_singolo_path}")

            # -- Schema.ini unico (append) --
            if CREA_SCHEMA_INI_UNICO:
                with open(schema_unico_path, 'a', encoding='utf-8') as uf:
                    scrivi_sezione_schema_ini(uf, csv_name, export_columns)

    except Exception as e:
        logging.error(f"ERRORE su {filename}: {e}")
        logging.debug(traceback.format_exc())
        nomi = estrai_nomi_campi_binari(file_path)
        logging.error(f"  Campi rilevati: {nomi}")

logging.info("=== PROCESSO DI ESPORTAZIONE TERMINATO ===")
input("Premi Invio per uscire...")
