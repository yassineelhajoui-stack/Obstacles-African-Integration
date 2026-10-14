# Obstacles to African integration – données et code de réplication

Données et code Python reproduisant l'ensemble des résultats du manuscrit
« Obstacles to African integration… » (révision soumise à *African Development Review*).

## Contenu
| Dossier / fichier | Description |
|---|---|
| `data_corrigee/ACP/ACP.xlsx` | Variables pays-année et indices ACP (feuille `indices_pays_annee`) |
| `data_corrigee/modeles_intra/*.xlsx` | 9 bases bilatérales intra-africaines (continent + 8 CER) |
| `data_corrigee/modeles_extra/*.xlsx` | 9 bases bilatérales extra-africaines |
| `00_…py` à `10_…py` | Étapes de l'analyse (importation, indices, gravité, potentiel, robustesse…) |
| `run_all.py` | Exécute toutes les étapes dans l'ordre |
| `resultats_reference/Tableaux_manuscrit.xlsx` | Tableaux de référence attendus |

Chaque base Excel comporte une feuille `Notes_corrections` décrivant les corrections apportées.

## Utilisation
```bash
git clone https://github.com/yassineelhajoui-stack/Obstacles-African-Integration.git
cd Obstacles-African-Integration
pip install -r requirements.txt
python run_all.py          # ou : python run_all.py 2  pour reprendre à l'étape 02
```
Les résultats sont écrits dans `resultats/` (tableau final : `resultats/Tableaux_manuscrit.xlsx`).
Le dossier `data_corrigee/` est détecté automatiquement ; sinon définir la variable d'environnement `DATA_DIR`.

Python ≥ 3.10, pyfixest ≥ 0.60. Durée totale : environ 30 à 60 minutes selon la machine.

## Citation
El Hajoui, Y. (2026). Obstacles to African integration… *African Development Review* (en révision).
