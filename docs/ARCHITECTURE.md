# Architecture du Projet

## Vue d'Ensemble

Ce projet détecte les anomalies sur les marchés crypto en temps réel.
```
[API Binance] → [Kafka] → [Spark Streaming] → [Modèles ML] → [Alertes]
```

Phase 1 : Python + données historiques
Phase 2 : Ajout Kafka + Spark + Docker

---

## Structure des Dossiers
```
market-anomaly-detection/
├── data/
│   ├── raw/                # Données brutes de Binance (ne pas modifier)
│   └── processed/          # Données nettoyées avec features
├── src/
│   ├── data_collection/    # Scripts collecte API Binance
│   ├── preprocessing/      # Nettoyage et feature engineering
│   ├── models/             # Les 4 modèles ML
│   ├── streaming/          # Kafka + Spark (Phase 2)
│   └── evaluation/         # Métriques et comparaisons
├── notebooks/              # Jupyter notebooks pour exploration
├── paper/
│   └── figures/            # Graphiques pour l'article IEEE
├── config/                 # Fichiers de configuration
└── docs/                   # Documentation du projet
```

---

## Description des Dossiers

### `data/raw/`

**Rôle** : Stocker les données brutes de l'API Binance.

**Contenu** :
- `BTCUSDT.csv` : Historique Bitcoin
- `ETHUSDT.csv` : Historique Ethereum

**Règle** : Ne jamais modifier ces fichiers. C'est la source de vérité.

---

### `data/processed/`

**Rôle** : Stocker les données transformées et prêtes pour les modèles.

**Contenu** :
- `BTCUSDT_features.csv` : Données avec features calculées
- `ETHUSDT_features.csv`
- `train.csv` : Données d'entraînement (80%)
- `test.csv` : Données de test (20%)

**Features calculées** :
| Feature | Description |
|---------|-------------|
| returns | Variation de prix (%) |
| volatility | Écart-type sur 20 périodes |
| z_score | Distance par rapport à la moyenne |
| rsi | Relative Strength Index |
| ma_20 | Moyenne mobile 20 périodes |

---

### `src/data_collection/`

**Rôle** : Récupérer les données depuis l'API Binance.

**Fichiers** :
| Fichier | Description |
|---------|-------------|
| `binance_client.py` | Connexion à l'API |
| `fetch_historical.py` | Télécharger l'historique |
| `fetch_realtime.py` | Données temps réel (Phase 2) |

---

### `src/preprocessing/`

**Rôle** : Nettoyer les données et créer les features.

**Fichiers** :
| Fichier | Description |
|---------|-------------|
| `cleaner.py` | Supprimer NaN, doublons, convertir timestamps |
| `feature_engineering.py` | Calculer returns, volatility, z_score, etc. |

**Flux** :
```
data/raw/ → cleaner.py → feature_engineering.py → data/processed/
```

---

### `src/models/`

**Rôle** : Implémenter les 4 algorithmes de détection d'anomalies.

**Fichiers** :
| Fichier | Modèle | Description |
|---------|--------|-------------|
| `zscore.py` | Z-Score | Méthode statistique simple |
| `isolation_forest.py` | Isolation Forest | Basé sur les arbres |
| `one_class_svm.py` | One-Class SVM | Support Vector Machine |
| `lstm_autoencoder.py` | LSTM Autoencoder | Deep Learning |

**Comparaison** :
| Modèle | Complexité | Vitesse | Multi-features | Temporel |
|--------|------------|---------|----------------|----------|
| Z-Score | ⭐ | ⚡⚡⚡ | ❌ | ❌ |
| Isolation Forest | ⭐⭐ | ⚡⚡ | ✅ | ❌ |
| One-Class SVM | ⭐⭐ | ⚡ | ✅ | ❌ |
| LSTM Autoencoder | ⭐⭐⭐ | 🐢 | ✅ | ✅ |

---

### `src/streaming/`

**Rôle** : Traitement temps réel avec Kafka et Spark (Phase 2).

**Fichiers** :
| Fichier | Description |
|---------|-------------|
| `kafka_producer.py` | Envoyer données vers Kafka |
| `kafka_consumer.py` | Lire depuis Kafka |
| `spark_streaming.py` | Traitement avec Spark |

**Architecture** :
```
API Binance → Kafka Producer → Kafka Topic → Spark Streaming → Modèles ML → Alertes
```

---

### `src/evaluation/`

**Rôle** : Mesurer et comparer les performances des modèles.

**Fichiers** :
| Fichier | Description |
|---------|-------------|
| `metrics.py` | Calculer precision, recall, F1-score |
| `compare_models.py` | Comparer les 4 modèles |
| `visualize_results.py` | Générer les graphiques |

**Métriques** :
| Métrique | Question |
|----------|----------|
| Precision | Parmi les alertes, combien sont vraies ? |
| Recall | Parmi les vraies anomalies, combien détectées ? |
| F1-Score | Équilibre precision/recall |

---

### `notebooks/`

**Rôle** : Expérimentation et tests rapides avec Jupyter.

**Fichiers** :
| Fichier | Description |
|---------|-------------|
| `01_data_exploration.ipynb` | Explorer les données brutes |
| `02_feature_analysis.ipynb` | Analyser les features |
| `03_model_experiments.ipynb` | Tester les modèles |
| `04_results_visualization.ipynb` | Graphiques finaux |

---

### `paper/figures/`

**Rôle** : Stocker les graphiques pour l'article IEEE.

**Contenu** :
- `architecture_diagram.png`
- `model_comparison.png`
- `anomalies_timeline.png`
- `confusion_matrix.png`
- `roc_curves.png`

---

### `config/`

**Rôle** : Centraliser la configuration.

**Fichiers** :
| Fichier | Description |
|---------|-------------|
| `config.yaml` | Paramètres généraux |
| `secrets.yaml` | Clés API (⚠️ dans .gitignore) |

---

### `docs/`

**Rôle** : Documentation du projet.

**Fichiers** :
| Fichier | Description |
|---------|-------------|
| `ARCHITECTURE.md` | Ce fichier |
| `DATA_COLLECTION.md` | Guide de collecte des données |
| `MODELS.md` | Documentation des modèles |
| `SETUP.md` | Instructions d'installation |

---

## Flux de Données Complet
```
                    PHASE 1 (Maintenant)
                    
API Binance ──→ data/raw/ ──→ src/preprocessing/ ──→ data/processed/
                                                            │
                                                            ↓
                                                     src/models/
                                                            │
                                                            ↓
                                                   src/evaluation/
                                                            │
                                                            ↓
                                                    paper/figures/


                    PHASE 2 (Plus tard)
                    
API Binance ──→ Kafka ──→ Spark Streaming ──→ Modèles ML ──→ Alertes
                              (src/streaming/)     (pré-entraînés)
```

---