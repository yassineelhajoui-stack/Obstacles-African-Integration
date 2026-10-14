# -*- coding: utf-8 -*-
"""Étape 4 : modèles de gravité augmentés des cinq indices (18 modèles).

- Tableau 6 : Afrique, intra et extra, sans effets fixes (spec. A, version précédente avec indices
  corrigés) et avec effets fixes pays + année (spec. B, spécification principale).
- Tableaux A4 et A5 : 16 modèles par CER (spec. B).
"""
from common import *

R = {}
for kind in ['intra', 'extra']:
    for rec in ORDER:
        d = load(kind, rec)
        for spec in (['A', 'B'] if rec == 'AFRIC' else ['B']):
            m, _ = estimate(kind, d, spec, rec=rec)
            R[(kind, rec, spec)] = result(m)
            print(kind, rec, spec, 'N =', m._N)
save(R, 'r04_augmentes')

iv = [x + s for s in ('_o', '_d') for x in IDX]
for kind in ['intra', 'extra']:
    rows = {}
    for rec in ORDER:
        t = R[(kind, rec, 'B')]['tidy']
        rows[rec] = {k: f"{t.loc[k, 'Estimate']:.3f}{stars(t.loc[k, 'Pr(>|t|)'])}" for k in iv if k in t.index}
        rows[rec]['N'] = R[(kind, rec, 'B')]['N']
    print('====', kind, 'spec B'); print(pd.DataFrame(rows).to_string())
