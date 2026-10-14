# -*- coding: utf-8 -*-
"""Étape 8 : statistiques descriptives (tableau 3), tests de diagnostic (tableau A6),
écarts-types intra-pays des indices et corrélations (texte §3.2)."""
from scipy.stats import chi2, norm
from common import *

out = {}
for kind in ['intra', 'extra']:
    d = load(kind, 'AFRIC'); v = rhs(kind, 'AFRIC')
    m, _ = estimate(kind, d, 'B')
    d2, cols, fe = country_fe(d, kind)
    used = d2.dropna(subset=v + ['TRD_Mll']).copy()
    assert len(used) == m._N, "échantillon d'estimation différent de l'échantillon complet"
    used['mu'] = np.asarray(m._Y_hat_response).flatten()
    used['y'] = np.asarray(m._Y_untransformed).flatten()
    used['xb'] = np.log(used.mu)

    # Test de type Park (Santos Silva & Tenreyro, 2006) : (y - mu)^2 = a * mu^lambda
    used['u2'] = (used.y - used.mu) ** 2; used['lnmu'] = np.log(used.mu)
    tp = pf.fepois("u2~lnmu", data=used, vcov={'CRV1': 'pair'}).tidy()
    out[f'park_{kind}'] = (tp.loc['lnmu', 'Estimate'], tp.loc['lnmu', 'Std. Error'])
    # Test RESET : carré de l'indice linéaire ajouté au modèle
    used['xb2'] = used.xb ** 2
    tr = pf.fepois("TRD_Mll~" + "+".join(v + cols + ['xb2']) + "|" + fe, data=used, vcov={'CRV1': 'pair'}).tidy()
    out[f'reset_{kind}'] = (tr.loc['xb2', 'Estimate'], tr.loc['xb2', 'Pr(>|t|)'])
    # Autocorrélation d'ordre 1 des résidus de Pearson
    used['pr'] = (used.y - used.mu) / np.sqrt(used.mu)
    used = used.sort_values(['pair', 'year']); used['pr_l'] = used.groupby('pair').pr.shift(1)
    ta = pf.feols("pr~pr_l", data=used.dropna(subset=['pr_l']), vcov={'CRV1': 'pair'}).tidy()
    out[f'ar1_{kind}'] = (ta.loc['pr_l', 'Estimate'], ta.loc['pr_l', 'Pr(>|t|)'])
    # Test CD de Pesaran sur les résidus de Pearson (paires observées au moins 80 % des années)
    Wm = used.pivot_table(index='year', columns='pair', values='pr')
    Wm = Wm.dropna(axis=1, thresh=int(0.8 * Wm.shape[0]))
    C = Wm.corr(min_periods=8).values; iu = np.triu_indices(C.shape[0], 1); c = C[iu]
    Tij = (Wm.notna().astype(int).T @ Wm.notna().astype(int)).values[iu]
    ok = ~np.isnan(c)
    CD = np.sqrt(2 / ok.sum()) * np.sum(np.sqrt(Tij[ok]) * c[ok])
    out[f'cd_{kind}'] = (CD, 2 * norm.sf(abs(CD)), C.shape[0])
    # Breusch–Pagan sur les résidus du modèle log-linéaire (flux positifs)
    lp = used[used.y > 0].copy(); lp['lny'] = np.log(lp.y)
    e2 = np.asarray(pf.feols("lny~" + "+".join(v + cols) + "|" + fe, data=lp, vcov='hetero').resid()) ** 2
    Xb = np.column_stack([np.ones(len(lp)), lp[v].values])
    fit = Xb @ np.linalg.lstsq(Xb, e2, rcond=None)[0]
    R2 = 1 - ((e2 - fit) ** 2).sum() / ((e2 - e2.mean()) ** 2).sum()
    out[f'bp_{kind}'] = (len(e2) * R2, Xb.shape[1] - 1, chi2.sf(len(e2) * R2, Xb.shape[1] - 1))
    # Facteurs d'inflation de la variance
    X = used[v].astype(float); X = (X - X.mean()) / X.std(); X = X.loc[:, X.std() > 0]
    out[f'vif_{kind}'] = pd.Series(np.diag(np.linalg.inv(np.corrcoef(X.T.values))), index=X.columns)
    # Statistiques descriptives (tableau 3)
    dv = ['TRD_Mll', 'ln_pib_o', 'ln_pib_d', 'ln_pop_o', 'ln_pop_d', 'ln_D', 'CC', 'LC', 'FC'] + \
         [x + '_o' for x in IDX] + ([x + '_d' for x in IDX] if kind == 'intra' else [])
    D = d[dv].astype(float)
    out[f'desc_{kind}'] = pd.DataFrame({'N': D.notna().sum(), 'Mean': D.mean(), 'SD': D.std(), 'Min': D.min(), 'Max': D.max()})
    out[f'zeros_{kind}'] = (d.TRD_Mll == 0).mean()
    print(kind, {k: val for k, val in out.items() if k.endswith(kind) and not isinstance(val, (pd.Series, pd.DataFrame))})

cy = country_year()
out['sd'] = pd.DataFrame({'overall': cy[IDX].std(),
                          'within': cy[IDX].sub(cy.groupby('iso3')[IDX].transform('mean')).std(),
                          'N': cy[IDX].notna().sum()})
gd = load_raw('extra', 'AFRIC')[['iso3_o', 'year', 'ln_pib_o', 'ln_pop_o']].drop_duplicates(['iso3_o', 'year'])
out['corr'] = cy.merge(gd.rename(columns={'iso3_o': 'iso3'}), on=['iso3', 'year'])[IDX + ['ln_pib_o', 'ln_pop_o']].corr()
print(out['sd']); print(out['corr'].round(2))
save(out, 'r08_diagnostics')
