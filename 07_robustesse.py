# -*- coding: utf-8 -*-
"""Étape 7 : tests de robustesse des modèles continentaux (tableaux 10, A7, A8) et robustesse par CER
(exclusion du Nigeria, de l'Afrique du Sud et de l'Égypte, §4.4).

Spécifications : base (EF pays + année), sans EF, EF année, EF paire + année, regroupement
bidimensionnel, indices retardés (1 et 3 ans), ACP alternative, indices équipondérés, exclusion de
grands pays / de pays en conflit, 2006–2019, hors 2020–2021, imputation d'INFRA, flux positifs,
MCO log-linéaires, commerce retardé, fonction de contrôle, flux orientés, Gamma PML.
"""
from common import *

# Régions de l'Union africaine (pour l'instrument « moyenne régionale hors pays »)
REG = {'North': ['DZA', 'EGY', 'LBY', 'MAR', 'MRT', 'TUN', 'ESH'],
       'West': ['BEN', 'BFA', 'CPV', 'CIV', 'GMB', 'GHA', 'GIN', 'GNB', 'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO'],
       'Central': ['AGO', 'BDI', 'CMR', 'CAF', 'TCD', 'COG', 'COD', 'GNQ', 'GAB', 'STP'],
       'East': ['COM', 'DJI', 'ERI', 'ETH', 'KEN', 'MDG', 'MUS', 'RWA', 'SYC', 'SOM', 'SSD', 'SDN', 'TZA', 'UGA'],
       'South': ['BWA', 'LSO', 'MWI', 'MOZ', 'NAM', 'ZAF', 'SWZ', 'ZMB', 'ZWE']}
REGION = {c: r for r, l in REG.items() for c in l}
BIG3 = ['ZAF', 'EGY', 'NGA']


def control_function_residuals():
    """Première étape (pays-année) : indice ~ retard de 2 ans + moyenne régionale hors pays
    + ln PIB + ln population | EF pays + année. Renvoie les résidus et les F de première étape."""
    cy = country_year().copy()
    cy['reg'] = cy.iso3.map(REGION)
    gdp = load_raw('extra', 'AFRIC')[['iso3_o', 'year', 'ln_pib_o', 'ln_pop_o']].drop_duplicates(['iso3_o', 'year'])
    cy = cy.merge(gdp.rename(columns={'iso3_o': 'iso3', 'ln_pib_o': 'lgdp', 'ln_pop_o': 'lpop'}), on=['iso3', 'year'], how='left')
    F = {}
    for v in IDX:
        cy[v + '_L2'] = cy.groupby('iso3')[v].shift(2)
        s = cy.groupby(['reg', 'year'])[v].transform('sum')
        n = cy.groupby(['reg', 'year'])[v].transform('count')
        cy[v + '_loo'] = (s - cy[v].fillna(0)) / (n - cy[v].notna().astype(int))
        sub = cy.dropna(subset=[v, v + '_L2', v + '_loo', 'lgdp', 'lpop'])
        # effets fixes pays absorbés (emboîtés dans les clusters pays) et indicatrices d'année explicites :
        # la correction de petit échantillon est ainsi déterministe (convention de reghdfe sous Stata)
        m = pf.feols(f"{v}~{v}_L2+{v}_loo+lgdp+lpop+C(year)|iso3", data=sub, vcov={'CRV1': 'iso3'})
        names = list(m._coefnames)
        ix = [names.index(v + '_L2'), names.index(v + '_loo')]
        b = m.coef().values[ix]
        Vb = m._vcov[np.ix_(ix, ix)]
        F[v] = float(b @ np.linalg.solve(Vb, b)) / 2          # statistique F de Wald (2 instruments)
        cy.loc[sub.index, v + '_v'] = np.asarray(m.resid()).flatten()
    return cy[['iso3', 'year'] + [v + '_v' for v in IDX]], F


def run(kind, d, spec='B', v=None, y='TRD_Mll', vcov=None):
    m, _ = estimate(kind, d, spec, v or rhs(kind, 'AFRIC'), y=y, vcov=vcov)
    return result(m)


def subst(v, mp):
    return [mp.get(x, x) for x in v]


def gpml(kind):
    """Gamma PML (flux positifs) par moindres carrés itérés : z = eta + (y - mu)/mu, poids unitaires,
    avec les mêmes effets fixes ; erreurs-types sandwich regroupées par paire."""
    d = load(kind, 'AFRIC'); v = rhs(kind, 'AFRIC')
    d, cols, fe = country_fe(d, kind)
    d = d.dropna(subset=v + ['TRD_Mll']); d = d[d.TRD_Mll > 0].copy()
    m0 = pf.fepois("TRD_Mll~" + "+".join(v + cols) + "|" + fe, data=d, vcov={'CRV1': 'pair'})
    eta = np.log(np.asarray(m0.predict(type='response')).flatten())
    y = d.TRD_Mll.values
    for it in range(500):
        mu = np.exp(eta)
        d['z'] = eta + (y - mu) / mu
        m = pf.feols("z~" + "+".join(v + cols) + "|" + fe, data=d, vcov={'CRV1': 'pair'})
        new = np.asarray(m.predict()).flatten()
        step = np.max(np.abs(new - eta))
        eta = 0.5 * eta + 0.5 * new          # pas amorti pour la stabilité
        if step < 1e-7:
            break
    return {'tidy': tidy(m), 'N': m._N, 'r2': np.nan, 'iterations': it}


res = {}
cfr, F = control_function_residuals()
cy = country_year()
mean_geot = cy.groupby('iso3').I_IPI.mean()
CONFLICT = mean_geot[mean_geot >= mean_geot.quantile(0.9)].index.tolist()
print('F de première étape :', {k: round(v, 1) for k, v in F.items()})
print('Pays les plus touchés par les conflits :', CONFLICT)

for kind in ['intra', 'extra']:
    sides = ('o', 'd') if kind == 'intra' else ('o',)
    d0 = load(kind, 'AFRIC'); v0 = rhs(kind, 'AFRIC'); R = {}
    R['base'] = run(kind, d0)
    R['pooled'] = run(kind, d0, 'A')
    R['yearFE'] = run(kind, d0, 'Y')
    R['pairFE'] = run(kind, d0, 'P')
    R['twoway_cl'] = run(kind, d0, vcov={'CRV1': 'iso3_o+iso3_d'})
    for L in (1, 3):
        R[f'lag{L}'] = run(kind, d0, v=subst(v0, {f'{x}_{s}': f'{x}L{L}_{s}' for x in IDX for s in sides}))
    mp = {}
    for s in sides:
        mp.update({f'I_GOV_{s}': f'I_GOVnoFDI_{s}', f'I_IDF_{s}': f'I_IDFnoCBDB_{s}',
                   f'I_IFC_{s}': f'I_IFCcost_{s}', f'I_infra_{s}': f'I_infraICT_{s}'})
    R['altPCA'] = run(kind, d0, v=subst(v0, mp))
    R['eqweight'] = run(kind, d0, v=subst(v0, {f'{x}_{s}': f'{x}_eq_{s}' for x in IDX for s in sides}))
    R['noBig3'] = run(kind, d0[~d0.iso3_o.isin(BIG3) & ~d0.iso3_d.isin(BIG3)])
    R['noConflict'] = run(kind, d0[~d0.iso3_o.isin(CONFLICT) & ~d0.iso3_d.isin(CONFLICT)])
    R['y2006_2019'] = run(kind, d0[(d0.year >= 2006) & (d0.year <= 2019)])
    R['noCovid'] = run(kind, d0[~d0.year.isin([2020, 2021])])
    R['positive'] = run(kind, d0[d0.TRD_Mll > 0])
    # MCO log-linéaires avec les mêmes effets fixes (flux positifs)
    dp = d0[d0.TRD_Mll > 0].copy(); dp['lnY'] = np.log(dp.TRD_Mll)
    dp, cols, fe = country_fe(dp, kind)
    mo = pf.feols("lnY~" + "+".join(v0 + cols) + "|" + fe, data=dp, vcov={'CRV1': 'pair'})
    R['OLSlog'] = {'tidy': tidy(mo), 'N': mo._N, 'r2': mo._r2}
    # commerce retardé
    d1 = d0.sort_values(['pair', 'year']).copy()
    d1['lag_lnY'] = np.log1p(d1.groupby('pair').TRD_Mll.shift(1))
    R['dynamic'] = run(kind, d1, v=v0 + ['lag_lnY'])
    # fonction de contrôle
    dc = d0.copy()
    for s in sides:
        dc = dc.merge(cfr.rename(columns={'iso3': 'iso3_' + s, **{x + '_v': x + '_v_' + s for x in IDX}}),
                      on=['iso3_' + s, 'year'], how='left')
    R['ctrlfun'] = run(kind, dc, v=v0 + [x + '_v_' + s for x in IDX for s in sides])
    # imputation des valeurs manquantes d'INFRA (0 = moyenne de l'indice) + indicatrice
    di = d0.copy(); vi = list(v0)
    for s in sides:
        di[f'miss_infra_{s}'] = di[f'I_infra_{s}'].isna().astype(float)
        di[f'I_infra_{s}'] = di[f'I_infra_{s}'].fillna(0)
        vi.append(f'miss_infra_{s}')
    R['imputeInfra'] = run(kind, di, v=vi)
    # flux orientés
    if kind == 'intra':
        a = d0.copy(); a['FLOW'] = a.EX_millon                 # exportations de i vers j
        b = swap(d0); b['FLOW'] = d0.IM_millon.values          # exportations de j vers i
        dd = pd.concat([a, b], ignore_index=True)
        dd['upair'] = dd[['iso3_o', 'iso3_d']].min(axis=1) + '_' + dd[['iso3_o', 'iso3_d']].max(axis=1)
        m = pf.fepois("FLOW~" + "+".join(v0) + "|iso3_o+iso3_d+year", data=dd, vcov={'CRV1': 'upair'})
        R['directed_exports'] = {'tidy': tidy(m), 'N': m._N, 'r2': np.nan}
    else:
        R['extra_exports'] = run(kind, d0, y='EX_millon')
        R['extra_imports'] = run(kind, d0, y='IM_millon')
    R['GPML'] = gpml(kind)
    res[kind] = R
    print(kind, 'terminé')

# Robustesse par CER : exclusion de ZAF, EGY, NGA dans les CER qui les contiennent
rec_big = {}
for kind in ['intra', 'extra']:
    for rec in ['SADC', 'CEDEAO', 'COMESA', 'CENSAD']:
        d = load(kind, rec)
        d = d[~d.iso3_o.isin(BIG3) & ~d.iso3_d.isin(BIG3)]
        m, _ = estimate(kind, d, 'B', rec=rec)
        rec_big[(kind, rec)] = result(m)
res['rec_big3'] = rec_big
res['F'] = F
res['conflict'] = CONFLICT
save(res, 'r07_robustesse')

for kind in ['intra', 'extra']:
    rows = {}
    for k, r in res[kind].items():
        t = r['tidy']
        rows[k] = {i: f"{t.loc[i, 'Estimate']:.3f}{stars(t.loc[i, 'Pr(>|t|)'])}" for i in t.index if i.startswith('I_')}
        rows[k]['N'] = r['N']
    print(kind); print(pd.DataFrame(rows).to_string())
