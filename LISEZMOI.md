# Code de reproduction – « Trade integration in Africa: Evidence on trade potential and structural constraints across Regional Economic Communities »

Ce dossier contient le code Python qui reproduit, à partir des **bases de données corrigées** (dossier `data_corrigee`), tous les résultats chiffrés du manuscrit révisé : tableaux 1 à 11, tableaux A3 à A8 de l'annexe, tests de Wald et chiffres cités dans le texte.

## 1. Installation

Python 3.10 ou plus récent. Dans un terminal, depuis ce dossier :

```
pip install -r requirements.txt
```

Versions utilisées pour produire le manuscrit : Python 3.13, pyfixest 0.60.0, pandas 3.0, numpy 2.5, scipy 1.18.

## 2. Emplacement des données

Le code lit les **bases corrigées**, placées dans le sous-dossier `data_corrigee` de votre dossier `data`. Le chemin par défaut est déjà défini dans `config.py` :

```
D:\doctora-11-\woord\article 3\word\article finale\african developpment banqke\data\data_corrigee
```

Le dossier contient les mêmes sous-dossiers et les mêmes noms de fichiers que l'original (`ACP`, `modeles_intra`, `modeles_extra`). Les indices vérifiés y sont déjà intégrés : aucune étape de correction n'est nécessaire. Chaque fichier comporte une feuille `Notes_corrections` qui décrit ce qui a été modifié. Si vos données sont ailleurs, modifiez `DATA_DIR` dans `config.py` ou définissez la variable d'environnement `DATA_DIR`. Les résultats sont écrits dans le sous-dossier `resultats/`.

## 3. Exécution

```
python run_all.py          # toute la chaîne (environ 3 minutes)
python run_all.py 4        # reprendre à partir de l'étape 4
python 04_modeles_augmentes.py   # une étape seule (les étapes 0 et 1 doivent avoir été exécutées)
```

## 4. Contenu des scripts et correspondance avec le manuscrit

| Script | Ce qu'il fait | Résultats du manuscrit |
|---|---|---|
| `config.py` | Chemins des données et des résultats | — |
| `common.py` | Chargement, harmonisation des noms de colonnes, remplacement des indices par les indices vérifiés, spécifications PPML (sans EF, EF année, EF pays + année, EF paire + année) | — |
| `00_import_donnees.py` | Conversion des 18 bases corrigées et de la feuille `indices_pays_annee` d'`ACP.xlsx` en Parquet | — |
| `01_indices_acp.py` | Diagnostics de l'ACP (KMO, Bartlett, valeurs propres, alpha de Cronbach, saturations) ; vérifie que les indices des 18 bases sont identiques aux scores ACP | Tableau 1, tableau A3, §3.2 |
| `02_gravite_base.py` | Modèles de gravité de base ; création et détournement de commerce | Tableau 4, §4.1 |
| `03_potentiel.py` | Potentiel commercial (références A et B) | Tableau 5, §4.1 |
| `04_modeles_augmentes.py` | Les 18 modèles augmentés (Afrique + 8 CER, intra et extra) | Tableau 6, tableaux A4 et A5 |
| `05_test_intra_extra.py` | Test groupé intra/extra avec EF exportateur-année, importateur-année et paire | Tableau 8 |
| `06_heterogeneite_marges.py` | Tests de Wald d'égalité entre CER ; marges extensive et intensive | §4.3, tableau 11 |
| `07_robustesse.py` | Robustesse : EF alternatifs, regroupement bidimensionnel, retards, fonction de contrôle (avec F de première étape), commerce retardé, ACP alternatives, exclusions de pays, sous-périodes, imputation, MCO log-linéaires, Gamma PML, flux orientés ; robustesse par CER sans NGA, ZAF, EGY | Tableau 10, tableaux A7 et A8, §4.4 |
| `08_diagnostics.py` | Statistiques descriptives ; tests de Park, RESET, Breusch–Pagan, autocorrélation, CD de Pesaran ; VIF ; écarts-types intra-pays ; corrélations | Tableau 3, tableau A6, §3.1–3.2 |
| `09_classification_effets.py` | Effets économiques d'un écart-type ; classification des contraintes par CER | Tableaux 7 et 9 |
| `10_export_excel.py` | Écrit tous les tableaux dans `resultats/Tableaux_manuscrit.xlsx` | Tous |
| `run_all.py` | Exécute les étapes dans l'ordre | — |

Le dossier `resultats_reference/` contient le classeur `Tableaux_manuscrit.xlsx` obtenu sur nos données. Il permet de vérifier que votre exécution donne les mêmes chiffres.

## 5. Remarques importantes

1. **Bases corrigées.** Par rapport aux fichiers d'origine, les colonnes d'indices `I_*` ont été remplacées par les indices recalculés à partir d'`ACP.xlsx`. Les originaux contenaient des signes inversés, des colonnes mal alignées et des valeurs manquantes remplacées par 0. Les valeurs manquantes sont désormais laissées vides. Les colonnes nécessaires aux tests de robustesse ont été ajoutées : indices alternatifs, moyennes équipondérées et retards. Dans `ACP.xlsx`, le code de Maurice, saisi « MRT » dans les feuilles GOV, IFC, INFRA et IPI, est corrigé en « MUS », et la feuille `indices_pays_annee` a été ajoutée.
2. **Vérification automatique.** L'étape 1 affiche « Indices des 18 bases identiques au panel : True » lorsque les bases sont conformes.
3. **Spécification principale.** PPML avec effets fixes pays et année. Pour les paires intra-africaines, qui ne sont pas orientées, l'effet fixe pays vaut 1 lorsque le pays est l'un des deux membres de la paire. Les erreurs-types sont regroupées par paire.
4. **Reproductibilité.** `run_all.py` fixe la graine de hachage de Python (`PYTHONHASHSEED=0`), ce qui rend les résultats identiques d'une exécution à l'autre. Pour la fonction de contrôle, la statistique F de première étape est calculée avec les effets fixes pays absorbés et des indicatrices d'année explicites (convention de `reghdfe` sous Stata).
5. **Précision numérique.** Selon la version de pyfixest, de très petites différences (de l'ordre de 10⁻⁴ ou moins) peuvent apparaître. Elles n'affectent pas les chiffres arrondis du manuscrit.
6. **Pseudo-R².** Il n'est pas calculé pour les modèles avec effets fixes paire, car pyfixest retire les paires sans commerce.
