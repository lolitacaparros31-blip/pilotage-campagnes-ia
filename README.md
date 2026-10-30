# Lumen : plateforme d'analyse de campagnes générée par IA (Streamlit)

Quatre espaces : **Tableau de bord**, **Campagnes**, **Assistant IA**, **Rapports**. La plateforme s'ouvre sur une démo (campagnes fictives d'un festival) ; on peut importer ses propres exports CSV/Excel dans le menu de gauche.
**100 % gratuit. L'IA recommande, l'humain décide. Aucune donnée n'est inventée.**

## Lancer sur son ordinateur (privé)
```
pip install -r requirements.txt
streamlit run app.py
```

## Publier gratuitement (lien web)
1. Créer un dépôt sur github.com (de préférence **privé**) et y envoyer ces fichiers.
2. Aller sur share.streamlit.io, se connecter avec GitHub, cliquer **Create app**.
3. Choisir le dépôt, la branche `main`, le fichier `app.py`, puis **Deploy**.
4. Pour restreindre l'accès : réglages de l'appli > Sharing > inviter uniquement votre e-mail
   (le nombre d'applis privées gratuites est limité : vérifier sur le site).

Ne mettez JAMAIS vos fichiers de données dans le dépôt (le `.gitignore` les exclut).

## Les fichiers
| Fichier | Rôle |
|---|---|
| `app.py` | L'interface Lumen : menu en 4 étapes, cartes de campagnes, assistante Mia |
| `graphiques.py` | Graphiques interactifs (survol, zoom) |
| `.streamlit/config.toml` | Thème aux couleurs Pantone A/W 26-27 |
| `NOTE_EXPLICATIVE.md` | Note explicative de l'épreuve |
| `moteur_analyse.py` | Le calcul (identique au notebook Colab) |
| `contexte.py` | Réglages, profils de campagne (`PROFILS`), lancement du moteur |
| `prevision.py` | Prévisions : courbe, meilleurs créneaux, objectif atteignable |

## Faire évoluer
| Je veux… | Je modifie… |
|---|---|
| Reconnaître un nouvel export | `ALIAS` dans `moteur_analyse.py` |
| Un nouvel indicateur | `kpis()` dans `moteur_analyse.py` |
| Un nouveau sujet (ex. association) | `PROFILS` dans `contexte.py` |
| Les noms des campagnes de démo | `CAMPAGNES_DEMO` dans `app.py` |
| Changer la méthode de prévision | `prevision.py` |

## Limites
Les prévisions prolongent le passé : en dessous de 8 semaines de données, l'outil refuse de prévoir.
Les statistiques ne prouvent pas la cause d'un résultat et ne voient pas le hors-ligne.

## Assistant IA avec Gemini (facultatif)
Sans clé, l'assistant fonctionne en mode simulé. Pour activer Gemini, ajouter dans Streamlit Cloud
(réglages de l'appli > **Secrets**) : `GEMINI_API_KEY = "votre_clé"`. La clé ne va JAMAIS dans le code ni sur GitHub.
Seuls des chiffres agrégés sont envoyés à Gemini, jamais les fichiers importés. Limite : 15 questions par visite.
