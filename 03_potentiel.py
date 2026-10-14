# -*- coding: utf-8 -*-
"""Étape 3 : potentiel commercial (tableau 5).

Référence A : modèle de gravité estimé sur le commerce Afrique–UE/États-Unis/Chine (PPML, effets
fixes année), utilisé pour prédire HORS ÉCHANTILLON le commerce intra-africain.
Référence B : même modèle estimé sur l'ensemble du commerce de l'Afrique (intra + extra).
Ratio = somme du commerce observé / somme du commerce prédit.
"""
from common import *

MEM = rec_members()
a = load_raw('intra', 'AFRIC'); a['INTRA'] = 1
e = load_raw('extra', 'AFRIC'); e['INTRA'] = 0
g = ["ln_pop_o", "ln_pop_d", "ln_pib_o", "ln_pib_d", "ln_D", "CC", "LC", "FC"]
keep = ['iso3_o', 'iso3_d', 'year', 'TRD_Mll', 'pair', 'INTRA'] + g
p = pd.concat([a[keep], e[keep]], ignore_index=True).dropna()


def ratios(hat):
    q = p.assign(hat=hat)
    r = {('Africa', 'intra'): q[q.INTRA == 1].TRD_Mll.sum() / q[q.INTRA == 1].hat.sum(),
         ('Africa', 'extra'): q[q.INTRA == 0].TRD_Mll.sum() / q[q.INTRA == 0].hat.sum()}
    for k, mem in MEM.items():
        s = q[(q.INTRA == 1) & q.iso3_o.isin(mem) & q.iso3_d.isin(mem)]
        r[(k, 'intra')] = s.TRD_Mll.sum() / s.hat.sum()
        s = q[(q.INTRA == 0) & q.iso3_o.isin(mem)]
        r[(k, 'extra')] = s.TRD_Mll.sum() / s.hat.sum()
    for per, (y0, y1) in {'2000-2019': (2000, 2019), '2020-2024': (2020, 2024)}.items():
        for it in (1, 0):
            s = q[(q.INTRA == it) & q.year.between(y0, y1)]
            r[('Africa ' + per, 'intra' if it else 'extra')] = s.TRD_Mll.sum() / s.hat.sum()
    return r


# Référence A (hors échantillon)
mA = pf.fepois("TRD_Mll~" + "+".join(g) + "|year", data=p[p.INTRA == 0], vcov={'CRV1': 'pair'})
hatA = np.asarray(mA.predict(newdata=p, type='response')).flatten()
# Référence B (norme commune)
mB = pf.fepois("TRD_Mll~" + "+".join(g) + "|year", data=p, vcov={'CRV1': 'pair'})
hatB = np.asarray(mB.predict(type='response')).flatten()
assert len(hatB) == len(p)

rA, rB = ratios(hatA), ratios(hatB)
rows = []
for k in ['Africa', 'SADC', 'EAC', 'IGAD', 'CEDEAO', 'COMESA', 'CENSAD', 'UMA', 'CEEAC', 'Africa 2000-2019', 'Africa 2020-2024']:
    rows.append({'Sample': k, 'Benchmark A intra (%)': round(100 * rA[(k, 'intra')], 1),
                 'Benchmark A extra (%)': round(100 * rA[(k, 'extra')], 1),
                 'Benchmark B intra (%)': round(100 * rB[(k, 'intra')], 1),
                 'Benchmark B extra (%)': round(100 * rB[(k, 'extra')], 1)})
t5 = pd.DataFrame(rows)
save({'table5': t5, 'benchA': tidy(mA), 'benchB': tidy(mB)}, 'r03_potentiel')
print(t5.to_string())
