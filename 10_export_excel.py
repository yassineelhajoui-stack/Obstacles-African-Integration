# -*- coding: utf-8 -*-
"""Étape 10 : export de tous les tableaux du manuscrit dans un classeur Excel
(resultats/Tableaux_manuscrit.xlsx). Cellules au format « coefficient étoiles (erreur-type) »."""
from common import *
from config import OUT_DIR

A = load_pkl('r01_acp'); B = load_pkl('r02_base'); P = load_pkl('r03_potentiel'); R = load_pkl('r04_augmentes')
H = load_pkl('r05_intra_extra'); M = load_pkl('r06_heterogeneite_marges'); RB = load_pkl('r07_robustesse')
D = load_pkl('r08_diagnostics'); C = load_pkl('r09_classification')


def cell(t, k, se=True):
    if t is None or k not in t.index or pd.isna(t.loc[k, 'Estimate']):
        return ''
    e, s, p = t.loc[k, 'Estimate'], t.loc[k, 'Std. Error'], t.loc[k, 'Pr(>|t|)']
    return f"{e:.3f}{stars(p)} ({s:.3f})" if se else f"{e:.3f}{stars(p)}"


def coef_table(results, keys=None, extra_rows=None):
    """results : dict nom_colonne -> {'tidy','N','r2'}"""
    keys = keys or list(dict.fromkeys(k for r in results.values() for k in r['tidy'].index))
    df = pd.DataFrame({c: [cell(r['tidy'], k) for k in keys] for c, r in results.items()}, index=keys)
    df.loc['Observations'] = [r['N'] for r in results.values()]
    df.loc['Pseudo-R2'] = [round(r['r2'], 3) if r.get('r2') == r.get('r2') and r.get('r2') is not None else '' for r in results.values()]
    return df


sheets = {}
sheets['T1_ACP'] = A['table1']
sheets['A3_saturations'] = A['tableA3']
sheets['Controle_indices'] = A['checks']
sheets['T3_descriptives'] = pd.concat({'intra': D['desc_intra'], 'extra': D['desc_extra']})
sheets['T4_gravite_base'] = coef_table({'(1) Intra, EF année': B['c1'], '(2) Intra, EF pays+année': B['c2'],
                                        '(3) Extra, EF année': B['c3'], '(4) Extra, EF pays+année': B['c4']})
sheets['T5_potentiel'] = P['table5']
sheets['T6_augmente_Afrique'] = coef_table({'(1) Intra, sans EF': R[('intra', 'AFRIC', 'A')], '(2) Intra, EF': R[('intra', 'AFRIC', 'B')],
                                            '(3) Extra, sans EF': R[('extra', 'AFRIC', 'A')], '(4) Extra, EF': R[('extra', 'AFRIC', 'B')]})
sheets['T7_effets_economiques'] = C['table7']
t8 = pd.DataFrame({rec: [cell(H[rec]['tidy'], x + '_oX') for x in IDX] + [H[rec]['N']] for rec in ORDER},
                  index=[x + ' x INTRA' for x in IDX] + ['Observations']).T
sheets['T8_test_intra_extra'] = t8
sheets['T9_classification'] = C['table9']
keys10 = [('intra', 'I_infra_o'), ('intra', 'I_infra_d'), ('intra', 'I_IDF_o'), ('intra', 'I_IPI_d'), ('extra', 'I_IPI_o'), ('extra', 'I_infra_o')]


def rob_name(spec, base):
    if spec in ('lag1', 'lag3'):
        return base[:-2] + f'L{spec[-1]}' + base[-2:]
    if spec == 'altPCA':
        mp = {'I_GOV': 'I_GOVnoFDI', 'I_IDF': 'I_IDFnoCBDB', 'I_IFC': 'I_IFCcost', 'I_infra': 'I_infraICT', 'I_IPI': 'I_IPI'}
        return mp[base[:-2]] + base[-2:]
    if spec == 'eqweight':
        return base[:-2] + '_eq' + base[-2:]
    return base


specs = ['base', 'pooled', 'yearFE', 'pairFE', 'twoway_cl', 'lag1', 'lag3', 'ctrlfun', 'dynamic', 'altPCA', 'eqweight', 'noBig3',
         'noConflict', 'y2006_2019', 'noCovid', 'imputeInfra', 'positive', 'OLSlog', 'GPML', 'directed_exports']
t10 = {}
for s in specs:
    t10[s] = {}
    for kind, k in keys10:
        sk = 'extra_exports' if (kind == 'extra' and s == 'directed_exports') else s
        r = RB[kind].get(sk)
        t10[s][f'{kind}: {k}'] = cell(r['tidy'], rob_name(s, k), se=False) if r else ''
sheets['T10_robustesse_synthese'] = pd.DataFrame(t10).T
iv = [x + s for s in ('_o', '_d') for x in IDX]
sheets['T11_marges'] = pd.DataFrame({
    'Intra extensive (MPL)': [cell(M['extensive_intra']['tidy'], k) for k in iv],
    'Intra intensive (PPML X>0)': [cell(M['intensive_intra']['tidy'], k) for k in iv],
    'Extra extensive (MPL)': [cell(M['extensive_extra']['tidy'], k) for k in iv],
    'Extra intensive (PPML X>0)': [cell(M['intensive_extra']['tidy'], k) for k in iv]}, index=iv)
sheets['Wald_CER'] = M['wald']
for kind, nm in [('intra', 'A4_CER_intra'), ('extra', 'A5_CER_extra')]:
    sheets[nm] = coef_table({rec: R[(kind, rec, 'B')] for rec in ORDER[1:]})
sheets['A6_diagnostics'] = pd.DataFrame([
    {'Model': kind, 'Park lambda': round(D[f'park_{kind}'][0], 3), 'Park SE': round(D[f'park_{kind}'][1], 4),
     'RESET coef': round(D[f'reset_{kind}'][0], 4), 'RESET p': round(D[f'reset_{kind}'][1], 3),
     'BP chi2': round(D[f'bp_{kind}'][0], 1), 'BP df': D[f'bp_{kind}'][1], 'BP p': D[f'bp_{kind}'][2],
     'AR(1) rho': round(D[f'ar1_{kind}'][0], 3), 'Pesaran CD': round(D[f'cd_{kind}'][0], 1), 'CD pairs': D[f'cd_{kind}'][2],
     'VIF max indices': round(D[f'vif_{kind}'][[c for c in D[f'vif_{kind}'].index if c.startswith('I_')]].max(), 2),
     'VIF max all': round(D[f'vif_{kind}'].max(), 2), 'Zero share': round(D[f'zeros_{kind}'], 3)} for kind in ['intra', 'extra']])
for kind, nm in [('intra', 'A7_robustesse_intra'), ('extra', 'A8_robustesse_extra')]:
    cols = {}
    for s, r in RB[kind].items():
        t = r['tidy']
        cols[s] = {k: cell(t, k) for k in t.index if k.startswith('I_') or k == 'lag_lnY'}
        cols[s]['Observations'] = r['N']
    sheets[nm] = pd.DataFrame(cols)
sheets['Robustesse_CER_hors_grands'] = coef_table({f'{k[0]} {k[1]}': v for k, v in RB['rec_big3'].items()})
sheets['Fonction_controle_F'] = pd.DataFrame({'First-stage F': RB['F'], 'Conflict countries': ', '.join(RB['conflict'])})
sheets['SD_correlations'] = pd.concat({'SD': D['sd'], 'corr': D['corr'].round(3)}, axis=1)

path = OUT_DIR / "Tableaux_manuscrit.xlsx"
with pd.ExcelWriter(path) as xw:
    for nm, df in sheets.items():
        df.to_excel(xw, sheet_name=nm[:31])
print('Classeur écrit :', path)
