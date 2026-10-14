# -*- coding: utf-8 -*-
"""Exécute toute la chaîne de reproduction dans l'ordre (environ 15 à 30 minutes)."""
import os, runpy, time, sys
from pathlib import Path

# Graine de hachage fixe : rend identiques d'une exécution à l'autre les corrections de petit
# échantillon de pyfixest pour les modèles à effets fixes paire (sinon écarts au 5e chiffre).
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

STEPS = ['00_import_donnees.py', '01_indices_acp.py', '02_gravite_base.py', '03_potentiel.py',
         '04_modeles_augmentes.py', '05_test_intra_extra.py', '06_heterogeneite_marges.py',
         '07_robustesse.py', '08_diagnostics.py', '09_classification_effets.py', '10_export_excel.py']
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0   # ex. « python run_all.py 2 » reprend à l'étape 2
for s in STEPS[start:]:
    t = time.time()
    print(f"\n===== {s} =====")
    runpy.run_path(str(here / s), run_name='__main__')
    print(f"----- {s} terminé en {time.time() - t:.0f} s")
