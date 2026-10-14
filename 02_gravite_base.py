# -*- coding: utf-8 -*-
"""Étape 2 : modèles de gravité de base (tableau 4) et décomposition création/détournement
de commerce (Viner, Carrère, Soloaga-Winters).

Colonnes du tableau 4 :
 (1) intra-africain, effets fixes année, indicatrices intra-bloc (BOTH) et extra-bloc (ONE)
 (2) intra-africain, effets fixes pays + année, indicatrices intra-bloc
 (3) extra-africain, effets fixes année, appartenance aux CER
 (4) extra-africain, effets fixes pays + année (appartenance aux CER absorbée)
"""
from common import *

MEM = rec_members()
d = load('intra', 'AFRIC')
for r in RECS:
    in_o, in_d = d.iso3_o.isin(MEM[r]), d.iso3_d.isin(MEM[r])
    d['BOTH_' + r] = (in_o & in_d).astype(float)     # les deux partenaires sont membres
    d['ONE_' + r] = (in_o ^ in_d).astype(float)      # un seul partenaire est membre

base_intra = [x for x in rhs('intra', 'AFRIC', aug=False) if x not in RECS]
res = {}
m, _ = estimate('intra', d, 'Y', base_intra + ['BOTH_' + r for r in RECS] + ['ONE_' + r for r in RECS])
res['c1'] = result(m)
m, _ = estimate('intra', d, 'B', base_intra + ['BOTH_' + r for r in RECS])
res['c2'] = result(m)
e = load('extra', 'AFRIC')
m, _ = estimate('extra', e, 'Y', rhs('extra', 'AFRIC', aug=False))
res['c3'] = result(m)
m, _ = estimate('extra', e, 'B', [x for x in rhs('extra', 'AFRIC', aug=False) if x not in RECS])
res['c4'] = result(m)
res['members'] = MEM
save(res, 'r02_base')
for k in ['c1', 'c2', 'c3', 'c4']:
    print(k, 'N =', res[k]['N'], 'pseudo-R2 =', round(res[k]['r2'], 3))
    print(res[k]['tidy'].round(3).to_string())
