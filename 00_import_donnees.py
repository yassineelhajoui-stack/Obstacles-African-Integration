# -*- coding: utf-8 -*-
"""Étape 0 : conversion des 18 bases bilatérales et du panel des indices (feuille indices_pays_annee
d'ACP.xlsx) en Parquet, pour une lecture plus rapide."""
import pandas as pd
from config import DATA_DIR, PQ_DIR, ACP_FILE, INTRA_FILES, EXTRA_FILES

for folder, files in (("modeles_intra", INTRA_FILES), ("modeles_extra", EXTRA_FILES)):
    for rec, name in files.items():
        path = DATA_DIR / folder / f"{name}.xlsx"
        d = pd.read_excel(path, sheet_name=0)
        d.columns = [str(c) for c in d.columns]
        d.to_parquet(PQ_DIR / f"{name}.parquet")
        print(f"{folder}/{name}: {d.shape}")

cy = pd.read_excel(ACP_FILE, sheet_name='indices_pays_annee')
cy.to_parquet(PQ_DIR / "indices_pays_annee.parquet")
print("indices_pays_annee:", cy.shape)
