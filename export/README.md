======= ITALIANO =======

Script per l'esportazione in batch di tabelle DBISAM (.dat) in formato CSV.
Legge tutti i file .dat in una cartella di origine e produce file .csv in una cartella di destinazione, mantenendo gli stessi nomi.
Gestisce automaticamente i tipi di campo supportati (STRING, INTEGER, DATE, TIME, TIMESTAMP, CURRENCY, BCD, BOOLEAN, FLOAT, AUTOINCREMENT, ecc.) ed esclude i campi binari (BLOB, GRAPHIC).
I tipi sconosciuti vengono segnalati nel log ed esportati come celle vuote, senza bloccare il processo.
Opzione per escludere le tabelle prive di record.
Genera un file di log dettagliato (esportazione.log) con errori, warning e riepilogo.

======= ENGLISH =======

Batch export script for DBISAM tables (.dat) to CSV format.
Reads all .dat files from a source folder and creates corresponding .csv files in a destination folder.
Automatically handles supported field types (STRING, INTEGER, DATE, TIME, TIMESTAMP, CURRENCY, BCD, BOOLEAN, FLOAT, AUTOINCREMENT, etc.) and skips binary fields (BLOB, GRAPHIC).
Unknown field types are logged as warnings and exported as empty cells, without interrupting the process.
Option to skip tables with no records.
Generates a detailed log file (esportazione.log) with errors, warnings and summary.
