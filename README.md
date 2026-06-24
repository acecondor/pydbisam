# PyDBISAM Extended

Fork di [PyDBISAM](https://github.com/alinville/pydbisam) di Aaron Linville.

## Modifiche principali

- Aggiunti i tipi mancanti: TIME, GRAPHIC, AUTOINC_LARGE, FIXEDCHAR.
- Gestione automatica dei tipi sconosciuti (non bloccano più l’apertura delle tabelle).
- Nuovo script `esporta.py` per esportare tutte le tabelle .dat in CSV.
- I campi BLOB e GRAPHIC vengono automaticamente esclusi dall’esportazione.

## Licenza

Questo progetto rimane sotto licenza ISC, come l’originale.

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
