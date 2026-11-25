#!/usr/bin/env python3
"""Construiește pachetul .nvda-addon din folderul addon/.

Utilizare:  python build.py
Rezultat:   dist/<name>-<version>.nvda-addon

Nu are dependențe externe (doar biblioteca standard Python 3).
"""

import configparser
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(ROOT, "addon")
DIST_DIR = os.path.join(ROOT, "dist")
SKIP_DIRS = {"__pycache__"}
SKIP_EXT = {".pyc", ".pyo"}


def read_manifest():
	path = os.path.join(ADDON_DIR, "manifest.ini")
	parser = configparser.ConfigParser(interpolation=None)
	with open(path, encoding="utf-8") as f:
		# manifest.ini nu are secțiuni; adăugăm una falsă pentru configparser.
		parser.read_string("[addon]\n" + f.read())
	m = parser["addon"]
	return m["name"].strip().strip('"'), m["version"].strip().strip('"')


def main():
	# Consola Windows poate folosi cp1252, care nu are diacritice românești (ș, ț).
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8", errors="replace")
	name, version = read_manifest()
	os.makedirs(DIST_DIR, exist_ok=True)
	out = os.path.join(DIST_DIR, "%s-%s.nvda-addon" % (name, version))
	count = 0
	with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
		for dirpath, dirnames, filenames in os.walk(ADDON_DIR):
			dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
			for fn in sorted(filenames):
				if os.path.splitext(fn)[1] in SKIP_EXT:
					continue
				full = os.path.join(dirpath, fn)
				arc = os.path.relpath(full, ADDON_DIR).replace(os.sep, "/")
				z.write(full, arc)
				count += 1
	print("Construit: %s (%d fișiere)" % (os.path.relpath(out, ROOT), count))
	return 0


if __name__ == "__main__":
	sys.exit(main())
