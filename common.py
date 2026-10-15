# -*- coding: utf-8 -*-
"""Fonctions communes : chargement des données, spécifications et estimation PPML.

Notation des variables (fichiers de données -> manuscrit) :
  TRD_Mll   -> X_ijt (commerce total, exportations + importations)
  ln_pib_o/d, ln_pop_o/d -> ln GDP_i/j, ln POP_i/j
  ln_D, FC, LC, CC (+ interactions FCLC, CCFC, CCLC, CCLCFC) -> ln DIST, CONTIG, LANG, COLONY
  I_infra, I_GOV, I_IDF, I_IPI, I_IFC -> INFRA, GOV, FIN, GEOT, BPCI
  fta_wto -> RTA ; ZLECAF_ -> AfCFTA ; UMA, SADC, ... -> appartenance aux CER
  suffixe _o = pays i ; suffixe _d = pays j
"""
import re
import pickle
import warnings
import numpy as np
import pandas as pd
import pyfixest as pf
from config import PQ_DIR, PKL_DIR, INTRA_FILES, EXTRA_FILES

warnings.filterwarnings("ignore")

IDX = ["I_GOV", "I_IDF", "I_IPI", "I_IFC", "I_infra"]
GEO = ["CC", "LC", "FC", "FCLC", "CCFC", "CCLC", "CCLCFC", "ln_D"]
RECS = ["UMA", "SADC", "EAC", "CEDEAO", "CEEAC", "CENSAD", "IGAD", "COMESA"]
ORDER = ['AFRIC', 'UMA', 'CEDEAO', 'COMESA', 'SADC', 'EAC', 'CEEAC', 'IGAD', 'CENSAD']
ALT = (['I_GOVnoFDI', 'I_GOV_eq', 'I_IDFnoCBDB', 'I_IDF_eq', 'I_IFCcost', 'I_IFCtime', 'I_IFC_eq',
        'I_infra_eq', 'I_infraICT', 'I_IPI_eq'] + [f'{v}L{L}' for v in IDX for L in (1, 3)])
EXPECTED_SIGN = {'I_GOV': 1, 'I_IDF': 1, 'I_infra': 1, 'I_IPI': -1, 'I_IFC': -1}


# ---------------------------------------------------------------- utilitaires
def save(obj, name):
    pickle.dump(obj, open(PKL_DIR / f"{name}.pkl", "wb"))


def load_pkl(name):
    return pickle.load(open(PKL_DIR / f"{name}.pkl", "rb"))


def stars(p):
    return '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''


def tidy(m):
    """Coefficients, erreurs-types et p-valeurs, sans les indicatrices pays (c_XXX)."""
    t = m.tidy()
    return t[~t.index.str.startswith('c_')][['Estimate', 'Std. Error', 'Pr(>|t|)']]


def pseudo_r2(m):
    """Pseudo-R² : carré de la corrélation entre commerce observé et ajusté."""
    try:
        y = np.asarray(m._Y_untransformed).flatten()
        yhat = np.asarray(m._Y_hat_response).flatten()
        return np.corrcoef(y, yhat)[0, 1] ** 2
    except ValueError:   # observations retirées par pyfixest (ex. paires sans commerce avec EF paire)
        return np.nan


# ---------------------------------------------------------------- données
def _standardise(d):
    """Harmonise les noms de colonnes (les fichiers utilisent I_GOV_O_, I_IPI_d__, ZLECAF...)."""
    ren = {}
    for c in d.columns:
        m = re.match(r'^(I_(?:GOV|IDF|IPI|IFC|infra))_([oOdD])_*$', c)
        if m:
            ren[c] = m.group(1) + '_' + m.group(2).lower()
    d = d.rename(columns=ren)
    if 'ZLECAF' in d.columns and 'ZLECAF_' not in d.columns:
        d = d.rename(columns={'ZLECAF': 'ZLECAF_'})
    d = d[d.iso3_o.notna() & d.iso3_d.notna()].copy()
    d['pair'] = d.iso3_o.astype(str) + '_' + d.iso3_d.astype(str)
    return d


def load_raw(kind, rec):
    """Base bilatérale (les indices ACP y sont déjà inclus)."""
    name = (INTRA_FILES if kind == 'intra' else EXTRA_FILES)[rec]
    return _standardise(pd.read_parquet(PQ_DIR / f"{name}.parquet"))


_CY = None


def country_year():
    """Panel pays-année des indices (feuille indices_pays_annee d'ACP.xlsx, importée à l'étape 0)."""
    global _CY
    if _CY is None:
        _CY = pd.read_parquet(PQ_DIR / "indices_pays_annee.parquet")
    return _CY


def load(kind, rec):
    """Échantillon bilatéral utilisé dans toutes les estimations."""
    return load_raw(kind, rec)


def rhs(kind, rec, aug=True):
    """Liste des régresseurs : gravité de base (+ indices et RTA si aug=True)."""
    v = ["ln_pop_o", "ln_pop_d", "ln_pib_o", "ln_pib_d"]
    if aug:
        v += ([x + "_d" for x in IDX] + [x + "_o" for x in IDX]) if kind == 'intra' else [x + "_o" for x in IDX]
        v += ["fta_wto"]
    v += GEO
    if rec == 'AFRIC':
        v += ["ZLECAF_"] + RECS
    return v


def country_fe(d, kind):
    """Effets fixes pays.
    - intra : les paires sont non orientées ; une indicatrice par pays vaut 1 si le pays est l'un
      des deux membres de la paire (effet fixe symétrique), + effets fixes année ;
    - extra : effets fixes pays africain, partenaire et année.
    """
    d = d.copy()
    if kind == 'intra':
        cs = sorted(set(d.iso3_o) | set(d.iso3_d))
        cols = []
        for c in cs[1:]:
            d['c_' + c] = ((d.iso3_o == c) | (d.iso3_d == c)).astype(float)
            cols.append('c_' + c)
        return d, cols, "year"
    return d, [], "iso3_o+iso3_d+year"


def estimate(kind, d, spec='B', vars_=None, rec='AFRIC', aug=True, y='TRD_Mll', vcov=None):
    """Estimation PPML.
    spec 'A' : sans effets fixes
    spec 'Y' : effets fixes année
    spec 'B' : effets fixes pays + année (spécification principale du manuscrit)
    spec 'P' : effets fixes paire + année (variables bilatérales invariantes retirées)
    Erreurs-types regroupées par paire (par défaut).
    """
    v = vars_ or rhs(kind, rec, aug)
    vcov = vcov or {'CRV1': 'pair'}
    if spec == 'A':
        f = f"{y}~" + "+".join(v)
    elif spec == 'Y':
        f = f"{y}~" + "+".join(v) + "|year"
    elif spec == 'B':
        d, cols, fe = country_fe(d, kind)
        f = f"{y}~" + "+".join(v + cols) + "|" + fe
    elif spec == 'P':
        f = f"{y}~" + "+".join([x for x in v if x not in GEO]) + "|pair+year"
    else:
        raise ValueError(spec)
    m = pf.fepois(f, data=d, vcov=vcov)
    return m, d


def result(m):
    return {'tidy': tidy(m), 'N': m._N, 'r2': pseudo_r2(m)}


def swap(d):
    """Inverse les rôles i et j (pour empiler une paire non orientée dans les deux sens)."""
    ren = {}
    for c in d.columns:
        if c.endswith('_o'):
            ren[c] = c[:-2] + '_d'
        elif c.endswith('_d'):
            ren[c] = c[:-2] + '_o'
    return d.rename(columns=ren)


def rec_members():
    """Liste des membres de chaque CER, tirée des échantillons intra-CER."""
    out = {}
    for r in RECS:
        d = load_raw('intra', r)
        out[r] = sorted(set(d.iso3_o) | set(d.iso3_d))
    return out
