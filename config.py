# -*- coding: utf-8 -*-
"""Paramètres communs : chemins des données et des résultats.

Modifiez DATA_DIR pour pointer vers le dossier des BASES CORRIGÉES (« data_corrigee »,
qui contient les sous-dossiers ACP, modeles_intra et modeles_extra), ou définissez la
variable d'environnement DATA_DIR avant d'exécuter les scripts.
Ces bases contiennent déjà les indices vérifiés : aucune étape de correction n'est nécessaire.
"""
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# Ordre de recherche : variable d'environnement DATA_DIR, puis dossier « data_corrigee »
# placé à côté du code (structure du dépôt GitHub), puis chemin local de l'auteur.
_CANDIDATS = [_HERE / "data_corrigee", _HERE.parent / "data_corrigee",
              Path(r"D:\doctora-11-\woord\article 3\word\article finale\african developpment banqke\data\data_corrigee")]
DATA_DIR = Path(os.environ["DATA_DIR"]) if "DATA_DIR" in os.environ else next(
    (p for p in _CANDIDATS if p.exists()), _CANDIDATS[0])
OUT_DIR = Path(os.environ.get("OUT_DIR", Path(__file__).resolve().parent / "resultats"))
PQ_DIR = OUT_DIR / "parquet"          # copies rapides des fichiers Excel
PKL_DIR = OUT_DIR / "pickles"         # résultats intermédiaires
for p in (OUT_DIR, PQ_DIR, PKL_DIR):
    p.mkdir(parents=True, exist_ok=True)

ACP_FILE = DATA_DIR / "ACP" / "ACP.xlsx"
# Fichiers bilatéraux : (dossier, nom du fichier) pour chaque échantillon
INTRA_FILES = {'AFRIC': 'afric_intra', 'UMA': 'UMA_intra', 'CEDEAO': 'CEDEAO_intra', 'COMESA': 'COMESA_intra',
               'SADC': 'SADC_Intra', 'EAC': 'CEA_intra', 'CEEAC': 'CEEAC_intra', 'IGAD': 'IGAD_intra',
               'CENSAD': 'CENSAD_intra'}
EXTRA_FILES = {'AFRIC': 'afric_extra', 'UMA': 'UMA_extra', 'CEDEAO': 'CODEAO_extra', 'COMESA': 'COMESA_extra',
               'SADC': 'SADC_extra', 'EAC': 'CEA_extra', 'CEEAC': 'CEEAC_extra', 'IGAD': 'IGDI_extra',
               'CENSAD': 'CENSAD_extra'}
