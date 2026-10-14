# -*- coding: utf-8 -*-
"""Étape 1 : diagnostics de l'analyse en composantes principales (ACP).

Produit :
  - Tableau 1 (KMO, Bartlett, valeurs propres, variance expliquée, alpha de Cronbach)
  - Tableau A3 (saturations des deux premières composantes)
  - deux vérifications :
      a) les scores recalculés sont identiques aux indices de la feuille indices_pays_annee ;
      b) les indices contenus dans les 18 bases corrigées sont identiques à ce panel.

Les bases corrigées contiennent déjà les indices ; cette étape ne modifie aucune donnée.
"""
import numpy as np
import pandas as pd
from numpy.linalg import eigh
from scipy.stats import chi2
from config import ACP_FILE
from common import IDX, ORDER, load_raw, country_year, save

SHEETS = {'infra': 'INFRA', 'GOV': 'GOV', 'IDF': 'IDF', 'IPI': 'IPI', 'IFC': 'IFC'}
INDICATORS = {
    'infra': ['éléc', 'int', 'Phon-fix', 'Phon-mobil', 'TRF', 'TRPT', 'SIS'],
    'GOV': ['IDE', 'CC', 'GE', 'IP', 'RQ', 'ED', 'VR'],
    'IDF': ['CP', 'PB', 'CBB', 'NGAB', 'CB-DB'],
    'IPI': ['NVP', 'NV', 'GC'],
    'IFC': ['CX', 'CX_bc', 'CX:dc', 'CM', 'CM_bc', 'CM_dc', 'DX', 'DM', 'TX', 'TX_bc', 'TX_dc', 'TM', 'TM_bc', 'TM_dc'],
}
NAMES = {'infra': 'INFRA', 'GOV': 'GOV', 'IDF': 'FIN', 'IPI': 'GEOT', 'IFC': 'BPCI'}


def pca(df, cols):
    """ACP sur indicateurs standardisés (matrice de corrélation), observations complètes uniquement."""
    X = df[cols].apply(pd.to_numeric, errors='coerce')
    ok = X.notna().all(axis=1)
    Z = (X[ok] - X[ok].mean()) / X[ok].std()
    R = np.corrcoef(Z.T)
    w, V = eigh(R)
    o = w.argsort()[::-1]
    w, V = w[o], V[:, o]
    if V[:, 0].sum() < 0:
        V = -V
    score = pd.Series(np.nan, index=df.index)
    score[ok] = Z.values @ V[:, 0]
    return score, w, V, R, Z


def kmo(R):
    Ri = np.linalg.inv(R)
    D = np.diag(1 / np.sqrt(np.diag(Ri)))
    P = -D @ Ri @ D
    np.fill_diagonal(P, 0)
    R0 = R.copy()
    np.fill_diagonal(R0, 0)
    return (R0 ** 2).sum() / ((R0 ** 2).sum() + (P ** 2).sum()), (R0 ** 2).sum(0) / ((R0 ** 2).sum(0) + (P ** 2).sum(0))


cy = country_year()
tab1, loads = [], []
for k, cols in INDICATORS.items():
    d = pd.read_excel(ACP_FILE, sheet_name=SHEETS[k])
    score, w, V, R, Z = pca(d, cols)
    n, p = Z.shape
    bart = -(n - 1 - (2 * p + 5) / 6) * np.log(np.linalg.det(R))
    df_b = p * (p - 1) / 2
    K, Kv = kmo(R)
    C = Z.cov().values
    alpha = p / (p - 1) * (1 - np.trace(C) / C.sum())
    tab1.append({'Index': NAMES[k], 'Indicators': p, 'Country-years': n, 'KMO': round(K, 3),
                 'Bartlett chi2': round(bart, 1), 'df': int(df_b), 'Bartlett p': chi2.sf(bart, df_b),
                 'Eigenvalue 1': round(w[0], 3), 'Eigenvalue 2': round(w[1], 3), 'Eigenvalue 3': round(w[2], 3),
                 'Var. explained PC1 (%)': round(100 * w[0] / p, 1), 'Eigenvalues > 1': int((w > 1).sum()),
                 'Cronbach alpha': round(alpha, 3)})
    for j, c in enumerate(cols):
        loads.append({'Index': NAMES[k], 'Indicator': c, 'Loading PC1': round(V[j, 0], 3),
                      'Loading PC2': round(V[j, 1], 3), 'KMO indicator': round(Kv[j], 3)})
    # vérification a) : score recalculé = indice du panel
    m = pd.DataFrame({'iso3': d['Pays'], 'year': d['Année'], 's': score}).merge(cy[['iso3', 'year', 'I_' + k]], on=['iso3', 'year'])
    diff = np.nanmax(np.abs(m['s'] - m['I_' + k]))
    print(f"{NAMES[k]}: écart maximal avec indices_pays_annee = {diff:.2e}")

print("Corrélation GOV / GOV sans IDE :", round(cy[['I_GOV', 'I_GOVnoFDI']].corr().iloc[0, 1], 3))

# vérification b) : indices des 18 bases = panel pays-année
checks = []
for kind in ['intra', 'extra']:
    for rec in ORDER:
        d = load_raw(kind, rec)
        for s in (('o', 'd') if kind == 'intra' else ('o',)):
            m = cy[['iso3', 'year'] + IDX].rename(columns={'iso3': 'iso3_' + s, **{v: v + '_ref' for v in IDX}})
            dd = d.merge(m, on=['iso3_' + s, 'year'], how='left')
            for v in IDX:
                a, b = dd[f'{v}_{s}'].astype(float), dd[v + '_ref'].astype(float)
                same = ((np.abs(a - b) < 1e-9) | (a.isna() & b.isna())).mean()
                checks.append({'kind': kind, 'REC': rec, 'variable': f'{v}_{s}', 'share_identical': round(same, 4)})
checks = pd.DataFrame(checks)
print("Indices des 18 bases identiques au panel :", bool((checks.share_identical == 1).all()))

save({'table1': pd.DataFrame(tab1), 'tableA3': pd.DataFrame(loads), 'checks': checks}, 'r01_acp')
print(pd.DataFrame(tab1).to_string())
