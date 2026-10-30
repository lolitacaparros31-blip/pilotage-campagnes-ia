"""Prépare l'environnement du moteur d'analyse (imports, profils, réglages) et l'exécute.

Le moteur (moteur_analyse.py) est le MÊME code que dans le notebook Colab :
une seule logique, deux interfaces. Pour faire évoluer l'outil, on modifie
moteur_analyse.py (ALIAS = nouveaux noms de colonnes, kpis() = nouveaux indicateurs)
ou PROFILS ci-dessous (nouveau sujet de campagne).
"""
import warnings, io, base64, contextlib, datetime as dt
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold, cross_val_predict

JOURS = {"Monday":"Lundi","Tuesday":"Mardi","Wednesday":"Mercredi","Thursday":"Jeudi","Friday":"Vendredi","Saturday":"Samedi","Sunday":"Dimanche"}
ORDRE_JOURS = list(JOURS.values())

# Profils : le système s'adapte au sujet par paramétrage, sans changer le code.
PROFILS = {
  "marque":      {"ton": "professionnel et clair", "regle": "Respecter la charte et les mentions légales publicitaires."},
  "politique":   {"ton": "factuel et sobre",        "regle": "Pas de micro-ciblage opaque. Transparence sur le financement. Validation humaine obligatoire."},
  "gastronomie": {"ton": "chaleureux et visuel",    "regle": "Respecter les allergènes et les mentions de l'offre."},
  "personnalité":{"ton": "personnel et authentique","regle": "Vérifier les droits à l'image. Surveiller la e-réputation."},
  "influenceur": {"ton": "naturel et spontané",     "regle": "Mentionner clairement les partenariats."},
}

REGLAGES_DEFAUT = dict(
    PROFIL="marque", OBJECTIF="conversion", BASE_ENGAGEMENT="portée", NB_ABONNES=5000,
    AGE_COMPARAISON_H=48, TOLERANCE_AGE_H=6, SEUIL_ECHANTILLON=20, OBJECTIF_MAPE=20, SEUIL_ALERTE_NEG=40,
    CANAL_NEW="instagram", FORMAT_NEW="image", JOUR_NEW="Mardi", SAISON_NEW="été", OFFRE_NEW="aucune",
    BUDGET_NEW=100, HEURE_NEW=18, DUREE_NEW=7,
    A_IMPRESSIONS=0, A_CLICS=0, B_IMPRESSIONS=0, B_CLICS=0, SIM_ON=False,
)

_MOTEUR = Path(__file__).with_name("moteur_analyse.py").read_text(encoding="utf-8")
_BASE = dict(globals())


CANAUX_CONNUS = {"instagram": "instagram", "tiktok": "tiktok", "google": "google ads", "facebook": "facebook", "linkedin": "linkedin",
                 "youtube": "youtube", "newsletter": "newsletter", "mailing": "newsletter", "twitter": "x", "snap": "snapchat"}
NOMS_CANAL = {"canal", "plateforme", "platform", "channel", "réseau", "reseau", "source"}


def preparer_fichiers(fichiers):
    """Si un export n'a pas de colonne « canal » (ex. un fichier par réseau), on la déduit du nom du fichier.
    Les données ne sont pas modifiées : on ajoute seulement une colonne."""
    sortie = {}
    NOMS_FORMAT = {"format", "type_contenu", "media_type", "type", "type_de_publication"}
    tous = {}
    for nom, contenu in (fichiers or {}).items():
        try:
            tous[nom] = {str(x).strip().lower().replace(" ", "_") for x in (pd.read_excel(io.BytesIO(contenu)) if nom.lower().endswith(("xls", "xlsx")) else pd.read_csv(io.BytesIO(contenu), sep=None, engine="python")).columns}
        except Exception:
            tous[nom] = set()
    un_format = any(v & NOMS_FORMAT for v in tous.values())
    for nom, contenu in (fichiers or {}).items():
        try:
            t = pd.read_excel(io.BytesIO(contenu)) if nom.lower().endswith(("xls", "xlsx")) else pd.read_csv(io.BytesIO(contenu), sep=None, engine="python")
            cols = {str(c).strip().lower().replace(" ", "_") for c in t.columns}
            modif = False
            if un_format and not (cols & NOMS_FORMAT):
                t["format"] = "non précisé"
                modif = True
            if not (cols & NOMS_CANAL):
                bas = nom.lower()
                canal = next((v for k, v in CANAUX_CONNUS.items() if k in bas), Path(nom).stem.split("-")[-1].replace("_", " ").strip().lower())
                t["canal"] = canal
                modif = True
            if modif:
                contenu = t.to_csv(index=False).encode("utf-8")
                nom = Path(nom).stem + ".csv"
        except Exception:
            pass          # fichier illisible : le moteur le signalera
        sortie[nom] = contenu
    return sortie


def analyser(fichiers, demo, reglages, commentaires_csv=None):
    """Exécute le moteur. Retourne (espace de noms avec tous les résultats, journal texte)."""
    ns = dict(_BASE)
    ns.update(REGLAGES_DEFAUT)
    ns.update(reglages)
    ns["P"] = PROFILS[ns["PROFIL"]]
    ns["DEMO_MODE"] = bool(demo)
    ns["FICHIERS"] = dict(fichiers or {}) if demo else preparer_fichiers(fichiers)
    ns["COMM_BRUT"] = pd.read_csv(io.BytesIO(commentaires_csv), sep=None, engine="python") if commentaires_csv else None
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(_MOTEUR, "moteur_analyse.py", "exec"), ns)
    except Exception as e:
        e.journal = buf.getvalue()
        raise
    return ns, buf.getvalue()
