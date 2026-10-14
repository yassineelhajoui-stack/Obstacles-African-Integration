# -*- coding: utf-8 -*-
"""Étape 9 : effets économiques (tableau 7) et classification des contraintes par CER (tableau 9).

Règle de classification (seuil de 10 %) :
  INTRA   : coefficient du signe attendu et significatif dans le modèle intra-CER (i ou j, sans
            coefficient significatif de signe opposé), mais pas dans le modèle extra-CER ;
            † si le test groupé (tableau 8) confirme un effet plus fort sur le commerce intra.
  EXTRA   : significatif avec le signe attendu seulement dans le modèle extra-CER.
  GENERAL : significatif avec le signe attendu dans les deux modèles.
  —       : aucun effet significatif du signe attendu ; ‡ au moins un coefficient significatif de signe opposé.
"""
from common import *

R = load_pkl('r04_augmentes'); H = load_pkl('r05_intra_extra'); D = load_pkl('r08_diagnostics')


def sig(t, k, a=0.1):
    if k not in t.index or pd.isna(t.loc[k, 'Estimate']) or t.loc[k, 'Pr(>|t|)'] >= a:
        return 0
    return int(np.sign(t.loc[k, 'Estimate']))


rows = {}
for rec in ORDER:
    ti, te, th = R[('intra', rec, 'B')]['tidy'], R[('extra', rec, 'B')]['tidy'], H[rec]['tidy']
    row = {}
    for x in ['I_infra', 'I_GOV', 'I_IDF', 'I_IPI', 'I_IFC']:
        e = EXPECTED_SIGN[x]
        si = [sig(ti, x + '_o'), sig(ti, x + '_d')]
        intra_ok = any(s == e for s in si) and not any(s == -e for s in si)
        intra_contra = any(s == -e for s in si)
        se = sig(te, x + '_o')
        if intra_ok and se == e:
            c = 'GENERAL'
        elif intra_ok:
            c = 'INTRA' + ('†' if sig(th, x + '_oX') == e else '')
        elif se == e:
            c = 'EXTRA'
        else:
            c = '—' + ('‡' if intra_contra or se == -e else '')
        row[x] = c
    rows[rec] = row
t9 = pd.DataFrame(rows).T.rename(columns={'I_infra': 'INFRA', 'I_GOV': 'GOV', 'I_IDF': 'FIN', 'I_IPI': 'GEOT', 'I_IFC': 'BPCI'})
print(t9.to_string())

# Tableau 7 : variation en % du commerce pour une amélioration d'un écart-type intra-pays
tb, te = R[('intra', 'AFRIC', 'B')]['tidy'], R[('extra', 'AFRIC', 'B')]['tidy']
rows7 = []
for x in ['I_infra', 'I_GOV', 'I_IDF', 'I_IPI', 'I_IFC']:
    w = D['sd'].loc[x, 'within']; e = EXPECTED_SIGN[x]
    r = {'Index': x, 'Within-country SD': round(w, 3)}
    for nm, t, k in [('Intra i (%)', tb, x + '_o'), ('Intra j (%)', tb, x + '_d'), ('Extra (%)', te, x + '_o')]:
        b, p = t.loc[k, 'Estimate'], t.loc[k, 'Pr(>|t|)']
        r[nm] = f"{100 * (np.exp(b * w * e) - 1):+.1f}{stars(p)}"
    rows7.append(r)
t7 = pd.DataFrame(rows7)
print(t7.to_string())
save({'table7': t7, 'table9': t9}, 'r09_classification')
