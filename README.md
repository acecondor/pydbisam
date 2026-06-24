# PyDBISAM Extended

Fork di [PyDBISAM](https://github.com/alinville/pydbisam) di Aaron Linville.

## Credits

- Original PyDBISAM library by Aaron Linville (https://github.com/alinville/pydbisam)
- Memo/Blob handling adapted from the fork by maxthoursie (https://github.com/maxthoursie/pydbisam)

## Modifiche principali

- Aggiunti i tipi mancanti: TIME, GRAPHIC, AUTOINC_LARGE, FIXEDCHAR.
- Gestione automatica dei tipi sconosciuti (non bloccano più l’apertura delle tabelle).
- Nuovo script `esporta.py` per esportare tutte le tabelle .dat in CSV.
- I campi BLOB e GRAPHIC vengono automaticamente esclusi dall’esportazione.

## Licenza

Questo progetto rimane sotto licenza ISC, come l’originale.

## Sviluppo

Questo fork è stato sviluppato con l'assistenza di DeepSeek AI per l’analisi dei tipi DBISAM, la stesura delle modifiche e la documentazione.
Tutto il codice è stato revisionato e testato manualmente.

# DBISAM to CSV Exporter

Batch export script for DBISAM tables (.dat) to CSV, based on
[PyDBISAM](https://github.com/alinville/pydbisam) by Aaron Linville.

## What's new in this fork

- **New field types**: `TIME`, `GRAPHIC`, `AUTOINC_LARGE`, `FIXEDCHAR`
- **Robust unknown type handling**: unknown field types no longer crash the parser – they are exported as empty cells and reported in the log
- **Automatic exclusion**: `BLOB` and `GRAPHIC` are never exported to CSV
- **Batch export script**: `esporta.py` converts all `.dat` files in a folder
- **Empty table option**: skip tables with zero records (configurable)

## Supported DBISAM field types

| Type ID | DBISAM Type      | Size  | Exported to CSV |
|---------|------------------|-------|-----------------|
| 1       | STRING           | var   | Yes             |
| 2       | DATE             | 4     | Yes             |
| 3       | BLOB             | var   | No (excluded)   |
| 4       | BOOLEAN          | 1     | Yes             |
| 5       | SHORT INTEGER    | 2     | Yes             |
| 6       | INTEGER          | 4     | Yes             |
| 7       | FLOAT            | 8     | Yes             |
| 10      | TIME             | 4     | Yes             |
| 11      | TIMESTAMP        | 8     | Yes             |
| 18      | AUTOINC LARGE    | 8     | Yes             |
| 5383    | CURRENCY         | 8     | Yes             |
| 5635    | BCD              | 8     | Yes             |
| 6659    | GRAPHIC          | var   | No (excluded)   |
| 7430    | AUTOINCREMENT    | 4     | Yes             |
| 7937    | FIXEDCHAR        | var   | Yes             |

Any **unknown type** (type ID not listed above) is logged and exported as an empty cell, so the export never breaks.

## Quick start

1. Clone the repository or download the `export` folder.
2. Open `export/esporta.py` and set:
   - `origine` → folder containing `.dat` files
   - `destinazione` → folder where `.csv` will be created
3. Run:
   ```bash
   python export/esporta.py

-------------------------------------------------   

PyDBISAM
========

PyDBISAM is a pure Python module to read and export data from DBISAM tables (from their `.dat` files). The scope of PyDBISAM is _not_ to provide a full database framework but merely to provide the ability to read the table structure and the raw table data.

DBISAM is an on-disk database with one file per table. The file format is proprietary. The basic structure is [documented here](NOTES.md).


CLI Usage
---------
PyDBISAM includes a simple CLI that can be used to dump the table structure or export the data to various formats (e.g.: CSV).

```shell
# pydbisam --dump-structure path/to/file.dat

# pydbisam --dump-csv path/to/file.dat
```


Code Usage
----------
The PyDBISAM class can be used for read-only access to the tables.
```python
from pydbisam import PyDBISAM

with PyDBISAM("path/to/file.dat") as db:
	print(", ".join(db.fields()))
	for row in db.rows():
		print(", ".join(map(str, row)))
```


Similar Projects
----------------

- [DBISAM-to-JSON](https://github.com/KrijnL/DBISAM-to-JSON)
  - Python 2/3 script to convert DBISAM to JSON (limited support for various column types).
