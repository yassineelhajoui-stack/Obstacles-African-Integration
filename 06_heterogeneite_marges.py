# -*- coding: utf-8 -*-
"""Étape 6 : hétérogénéité entre CER (tests de Wald, §4.3) et marges extensive/intensive (tableau 11)."""
from scipy.stats import chi2
from common import *

out = {}
MEM = rec_members()
d = load('intra', 'AFRIC')
for r in RECS:
    d['BOTH_' + r] = (d.iso3_o.isin(MEM[r]) & d.iso3_d.isin(MEM[r])).astype(float)

# --- Tests de Wald : indice moyen des deux partenaires × appartenance à chaque CER
terms = []
for x in IDX:
    d[x + '_avg'] = (d[x + '_o'] + d[x + '_d']) / 2
    for r in RECS:
        d[f'{x}_x_{r}'] = d[x + '_avg'] * d['BOTH_' + r]
        terms.append(f'{x}_x_{r}')
m, _ = estimate('intra', d, 'B', rhs('intra', 'AFRIC') + terms)
b, V, names = m.coef().values, m._vcov, list(m._coefnames)
W = []
for x in IDX:
    ix = [names.index(f'{x}_x_{r}') for r in RECS if f'{x}_x_{r}' in names]
    k = len(ix)
    Rm = np.zeros((k - 1, len(names)))
    for i in range(k - 1):
        Rm[i, ix[i]], Rm[i, ix[i + 1]] = 1, -1
    rb = Rm @ b
    w = float(rb @ np.linalg.solve(Rm @ V @ Rm.T, rb))
    W.append({'Index': x, 'Wald chi2 (equality)': round(w, 1), 'df': k - 1, 'p-value': chi2.sf(w, k - 1)})
out['wald'] = pd.DataFrame(W)
print(out['wald'].to_string())

# --- Marge extensive : modèle de probabilité linéaire de 1(X>0), effets fixes pays + année
# --- Marge intensive : PPML sur les flux positifs (même spécification que le tableau 6, col. 2 et 4)
for kind in ['intra', 'extra']:
    dd = load(kind, 'AFRIC')
    dd['pos'] = (dd.TRD_Mll > 0).astype(float)
    v = rhs(kind, 'AFRIC')
    d2, cols, fe = country_fe(dd, kind)
    ml = pf.feols("pos~" + "+".join(v + cols) + "|" + fe, data=d2, vcov={'CRV1': 'pair'})
    out[f'extensive_{kind}'] = {'tidy': tidy(ml), 'N': ml._N}
    mi, _ = estimate(kind, dd[dd.TRD_Mll > 0], 'B')
    out[f'intensive_{kind}'] = result(mi)
    print(kind, 'extensive'); print(out[f'extensive_{kind}']['tidy'].filter(like='I_', axis=0).round(4))
save(out, 'r06_heterogeneite_marges')
