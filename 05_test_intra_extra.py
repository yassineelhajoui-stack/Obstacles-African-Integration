# -*- coding: utf-8 -*-
"""Étape 5 : test formel intra- versus extra-africain (tableau 8).

Pour chaque échantillon (Afrique et chaque CER), on empile :
  - les flux intra (paires non orientées prises dans les deux sens, i -> j et j -> i),
  - les flux extra du pays africain avec l'UE, les États-Unis et la Chine.
PPML avec effets fixes exportateur-année, importateur-année et paire ; régresseurs : indice du pays i
× INTRA. Le coefficient mesure la différence entre l'effet intra et l'effet extra, net de la
résistance multilatérale. Erreurs-types regroupées par paire non orientée.
"""
from common import *

GEO_KEEP = ['iso3_o', 'iso3_d', 'year', 'TRD_Mll', 'upair', 'INTRA'] + [c + '_o' for c in IDX]


def pooled(rec):
    a = load('intra', rec); a['upair'] = a.iso3_o + '_' + a.iso3_d
    intra = pd.concat([a, swap(a)], ignore_index=True); intra['INTRA'] = 1
    e = load('extra', rec); e['upair'] = e.iso3_o + '_' + e.iso3_d; e['INTRA'] = 0
    p = pd.concat([intra[GEO_KEEP], e[GEO_KEEP]], ignore_index=True)
    p['dpair'] = p.iso3_o + '>' + p.iso3_d
    for c in IDX:
        p[c + '_oX'] = p[c + '_o'] * p['INTRA']
    return p


out = {}
for rec in ORDER:
    p = pooled(rec)
    m = pf.fepois("TRD_Mll~" + "+".join(c + '_oX' for c in IDX) + "|iso3_o^year+iso3_d^year+dpair",
                  data=p, vcov={'CRV1': 'upair'})
    out[rec] = {'tidy': tidy(m), 'N': m._N}
    t = out[rec]['tidy']
    print(rec, m._N, ' '.join(f"{i}:{t.loc[i, 'Estimate']:.3f}{stars(t.loc[i, 'Pr(>|t|)'])}" for i in t.index))
save(out, 'r05_intra_extra')
