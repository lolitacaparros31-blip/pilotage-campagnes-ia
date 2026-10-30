"""Plateforme d'analyse de campagnes générée par IA : interface Streamlit.

Lancer en local :  streamlit run app.py
Quatre espaces : Tableau de bord, Campagnes, Assistant IA, Rapports.
Principe : l'IA recommande, l'humain décide. Aucune donnée n'est inventée.
"""
import re
import base64
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

from contexte import analyser, PROFILS, ORDRE_JOURS
import prevision as prev
import graphiques as gr

# Palette Pantone A/W 26-27, chaque couleur a un rôle unique
POSEIDON = "#123955"   # structure : titres, navigation, texte (confiance, lisibilité)
EGRET = "#F3ECE0"      # fond : neutre chaud, repose l'œil
FUCHSIA = "#9E2C6A"    # accent : actions et Assistant IA (ce qui demande l'attention)
ALL_ABOARD = "#5D9BCB" # données et prévisions
NEPTUNE = "#7FBB9E"    # positif : point fort, au-dessus de la moyenne
ACACIA = "#DACD65"     # vigilance : à surveiller, échantillon fragile, fonction simulée
SPICE = "#884332"      # alerte : difficulté, en dessous de la moyenne
GRIS = "#5B6470"
PAL = [ALL_ABOARD, FUCHSIA, NEPTUNE, "#755139", "#D29380", POSEIDON, "#B98391", "#646049"]

from pathlib import Path
MIA_IMG = Path(__file__).with_name("assets") / "mia.jpg"
try:
    MIA_B64 = base64.b64encode(MIA_IMG.read_bytes()).decode()
except Exception:
    MIA_B64 = ""

NOM_PLATEFORME = "Plateforme d'analyse de campagnes générée par IA"

st.set_page_config(page_title="Lumen · Analyse de campagnes par IA", page_icon="💡", layout="wide")
SERIF = "Georgia, 'Times New Roman', serif"
st.markdown(f"""
<style>
div.block-container {{max-width:100% !important;padding:2.2rem 3rem 3rem !important}}
section[data-testid="stSidebar"] {{min-width:300px}}
h1, h2, h3, .pt, .lumen {{font-family:{SERIF} !important; color:{POSEIDON}}}
.pt {{font-size:34px;margin:2px 0 0;font-weight:600}} .ps {{color:{GRIS};margin:0 0 14px}}
.eyebrow {{letter-spacing:.14em;text-transform:uppercase;font-size:11px;color:{FUCHSIA};font-weight:700;margin-top:6px}}
div[data-testid="stMetric"] {{background:#fff;border-radius:18px;padding:12px 16px;box-shadow:0 4px 16px rgba(18,57,85,.06)}}
div[data-testid="stMetricValue"] {{color:{POSEIDON};font-family:{SERIF}}}
.stTabs button[role="tab"] p {{font-size:16px;font-weight:600}}
.badge {{display:inline-block;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:bold}}
.demo, .simule {{background:#EFE6A8;color:#4A4320}} .ia {{background:#F1DCE7;color:{FUCHSIA}}}
.carte {{background:#fff;border-radius:16px;padding:14px 18px;margin:6px 0;box-shadow:0 3px 12px rgba(18,57,85,.06)}}
.carte.fort {{border-left:6px solid {NEPTUNE}}} .carte.faible {{border-left:6px solid {SPICE}}}
.carte.ia {{border-left:6px solid {FUCHSIA};color:{POSEIDON}}} .carte.info {{border-left:6px solid {ALL_ABOARD}}}
.carte.vigil {{border-left:6px solid {ACACIA}}} .carte.moyen {{border-left:6px solid {ALL_ABOARD}}}
.carte b {{color:{POSEIDON}}}
/* Lumen : marque et navigation */
.lumen {{font-size:30px;font-weight:600;margin:0;line-height:1}}
.slogan {{color:{FUCHSIA};font-style:italic;font-size:13px;margin:4px 0 2px}} .officiel {{color:{GRIS};font-size:11px;line-height:1.3}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] {{background:rgba(255,255,255,.55);border-radius:16px;padding:11px 14px;border:1px solid transparent;width:100%;margin-bottom:8px}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {{background:#fff}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] {{background:#fff;border-color:{FUCHSIA};box-shadow:0 4px 12px rgba(158,44,106,.15)}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {{display:none}}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] p {{font-size:15px;font-weight:600;color:{POSEIDON}}}
/* Mia */
.mia {{display:flex;gap:16px;background:#fff;border-radius:22px;padding:18px 22px;margin:8px 0 16px;box-shadow:0 6px 22px rgba(158,44,106,.12);border:1px solid #F1DCE7}}
.mia-av {{position:relative;flex:0 0 72px;height:72px;border-radius:50%;background:#F1DCE7 center/cover no-repeat;border:3px solid #fff;box-shadow:0 3px 10px rgba(158,44,106,.25)}}
.mia-av .mood {{position:absolute;right:-6px;bottom:-4px;font-size:20px;background:#fff;border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(18,57,85,.2)}}
.mia-nom {{font-family:{SERIF};font-weight:700;color:{FUCHSIA};font-size:15px;margin-bottom:4px}} .mia-txt {{color:{POSEIDON};line-height:1.55;font-size:15px}}
/* cartes de campagnes et priorités */
.cc {{background:#fff;border-radius:20px;padding:16px 18px;box-shadow:0 4px 16px rgba(18,57,85,.07);min-height:250px;border-top:5px solid {ALL_ABOARD}}}
.cc.fort {{border-top-color:{NEPTUNE}}} .cc.faible {{border-top-color:{SPICE}}} .cc.moyen {{border-top-color:{ALL_ABOARD}}}
.cc-t {{display:flex;align-items:center;gap:8px;margin-bottom:8px}} .cc-n {{font-weight:700;color:{POSEIDON}}}
.cc-v {{font-family:{SERIF};font-size:34px;color:{POSEIDON};margin-top:8px}} .cc-s {{color:{GRIS};font-size:12px;margin-bottom:8px}}
.cc-r {{background:#F7F1E8;border-radius:12px;padding:8px 10px;font-size:13px;color:{POSEIDON}}}
.statut {{display:inline-block;padding:2px 10px;border-radius:99px;font-size:12px;font-weight:600;background:#F3ECE0;color:{POSEIDON}}}
.reseau {{display:inline-flex;vertical-align:middle;margin-right:2px}}
.prio {{background:#fff;border-radius:18px;padding:14px 18px;min-height:150px;box-shadow:0 4px 16px rgba(18,57,85,.07)}}
.prio.fort {{border-left:6px solid {NEPTUNE}}} .prio.faible {{border-left:6px solid {SPICE}}} .prio.moyen {{border-left:6px solid {ACACIA}}}
.prio-t {{font-family:{SERIF};font-weight:700;color:{POSEIDON};margin-bottom:4px}} .prio-n {{color:{FUCHSIA};font-weight:700;margin-right:6px}}
</style>
""", unsafe_allow_html=True)

LOGO = f"""<div style="display:flex;align-items:center;gap:10px"><svg viewBox="0 0 32 32" width="38" height="38"><circle cx="16" cy="16" r="6" fill="{FUCHSIA}"/><g stroke="{POSEIDON}" stroke-width="2" stroke-linecap="round"><path d="M16 3v4M16 25v4M3 16h4M25 16h4M7 7l2.8 2.8M22.2 22.2L25 25M7 25l2.8-2.8M22.2 9.8L25 7"/></g></svg><div class="lumen">Lumen</div></div><div class="slogan">Vos campagnes, enfin lisibles.</div><div class="officiel">{NOM_PLATEFORME}</div>"""


def titre_page(titre, sous=""):
    st.markdown(f'<div class="eyebrow">Lumen</div><h2 class="pt">{titre}</h2><p class="ps">{sous}</p>', unsafe_allow_html=True)


def md(texte):
    return texte.replace("<b>", "**").replace("</b>", "**")


def espace(n):
    return f"{n:,.0f}".replace(",", " ")


def carte(texte, style="info"):
    st.markdown(f'<div class="carte {style}">{texte}</div>', unsafe_allow_html=True)


def badge(texte, style="simule"):
    return f'<span class="badge {style}">{texte}</span>'


# ------------------------------------------------------------------ navigation, données, réglages
PAGES = ["bord", "camp", "mia", "rapport"]
LIBELLES = {"bord": "① Tableau de bord", "camp": "② Campagnes", "mia": "③ Assistant IA · Mia", "rapport": "④ Rapports"}


def aller(page, fiche=None):
    st.session_state["page"] = page
    if fiche:
        st.session_state["fiche"] = fiche


with st.sidebar:
    st.markdown(LOGO, unsafe_allow_html=True)
    st.write("")
    page = st.radio("Navigation", PAGES, format_func=LIBELLES.get, key="page", label_visibility="collapsed")
    st.divider()
    st.markdown("##### Mes données")
    st.caption("Sans fichier, Lumen affiche une démonstration avec des données fictives.")
    fichiers_up = st.file_uploader("Exports CSV ou Excel (réseaux sociaux, publicité, site…)",
                                   type=["csv", "xls", "xlsx"], accept_multiple_files=True)
    comm_up = st.file_uploader("Commentaires (facultatif, CSV)", type=["csv"], key="comm")
    with st.expander("Quelles colonnes sont reconnues ?"):
        st.markdown("""
| Colonne | Noms reconnus |
|---|---|
| **canal** | canal, plateforme, platform |
| **date** | date, published |
| **impressions / portée** | impressions, reach, portée |
| clics, likes… | clicks, likes, comments |
| budget, conversions | spend, purchases |
| campagne | campagne, campaign |

Une colonne manquante est signalée, jamais devinée.""")
    with st.expander("Réglages"):
        profil = st.selectbox("Sujet de la campagne", list(PROFILS), help="Adapte le ton conseillé et les règles de conformité.")
        objectif = st.selectbox("Objectif principal", ["notoriété", "engagement", "trafic", "conversion", "fidélisation"], index=3,
                                help="Choisit l'indicateur que l'IA suit en priorité.")
        base = st.selectbox("Taux d'engagement calculé sur", ["portée", "abonnés", "vues"], help="La portée est conseillée : elle reflète les personnes réellement touchées.")
        nb_abonnes = st.number_input("Nombre d'abonnés (si base = abonnés)", 0, 10**9, 5000, step=100)
        age = st.number_input("Comparer les publications à l'âge (heures)", 1, 720, 48)
        tol = st.number_input("Tolérance (± heures)", 0, 72, 6)
        seuil = st.number_input("Seuil « échantillon fragile » (publications)", 5, 200, 20)
        mape = st.number_input("Erreur de prévision visée (%)", 5, 100, 20)
        alerte = st.number_input("Alerte si commentaires négatifs ≥ (%)", 10, 90, 40)
    st.caption("100 % gratuit · vos fichiers ne sont pas enregistrés par l'appli.")

REGLAGES = dict(PROFIL=profil, OBJECTIF=objectif, BASE_ENGAGEMENT=base, NB_ABONNES=int(nb_abonnes),
                AGE_COMPARAISON_H=int(age), TOLERANCE_AGE_H=int(tol), SEUIL_ECHANTILLON=int(seuil),
                OBJECTIF_MAPE=int(mape), SEUIL_ALERTE_NEG=int(alerte))


@st.cache_resource(show_spinner=False, max_entries=6)
def calculer(fichiers_t, demo, reglages_t, comm):
    return analyser(dict(fichiers_t), demo, dict(reglages_t), comm)


fichiers = tuple(sorted((f.name, f.getvalue()) for f in (fichiers_up or [])))
mode = "import" if fichiers else "demo"
comm_bytes = comm_up.getvalue() if comm_up is not None else None

try:
    with st.spinner("L'IA analyse les campagnes…"):
        ns, journal = calculer(fichiers, mode == "demo", tuple(sorted(REGLAGES.items())), comm_bytes)
except Exception as e:
    st.error(f"L'analyse n'a pas pu aboutir : {type(e).__name__} : {e}")
    st.caption("Retirez vos fichiers dans le menu de gauche pour revenir à la démo.")
    with st.expander("Détails"):
        st.code(getattr(e, "journal", "") or str(e))
    st.stop()

DF = ns["DF"].copy()
CIBLE = ns["CIBLE"]
NOMS = {"portee": "portée", "interactions": "interactions", "clics": "clics", "conversions": "conversions", "impressions": "impressions"}
nom_cible = NOMS.get(CIBLE, CIBLE)
METRIQUE = ns["METRIQUE_PRINCIPALE"]
NOM_M = ns["NOM_M"]
fm = ns["fm"]
SEUIL = ns["SEUIL_ECHANTILLON"]

# Campagnes : colonne « campagne » si l'export la contient, sinon une campagne par canal.
# En démo : trois à six campagnes fictives pour le lancement d'un festival (exemple du sujet).
CAMPAGNES_DEMO = {"instagram": "Notoriété · Instagram", "tiktok": "Public jeune · TikTok", "linkedin": "Partenaires · LinkedIn",
                  "facebook": "Communauté · Facebook", "youtube": "Teasers vidéo · YouTube", "newsletter": "Billetterie · Newsletter"}
col_camp = next((c for c in DF.columns if str(c).lower() in ("campagne", "campaign", "campaign_name", "nom_campagne")), None)
if col_camp:
    DF["campagne"] = DF[col_camp].astype(str)
elif mode == "demo":
    DF["campagne"] = DF["canal"].map(CAMPAGNES_DEMO).fillna(DF["canal"].astype(str))
else:
    DF["campagne"] = DF["canal"].astype(str).str.capitalize()

# ------------------------------------------------------------------ calculs d'affichage par campagne
TAUX = {"ctr": "CTR", "taux_conversion": "Taux de conversion", "taux_engagement": "Taux d'engagement", "cpa": "Coût / action (€)", "roas": "ROAS"}
VOLUMES = {"impressions": "Impressions", "portee": "Portée", "clics": "Clics", "conversions": "Conversions", "budget": "Budget (€)", "revenu": "Revenu (€)"}


def synthese_campagnes(d):
    """Volumes = sommes ; taux = médianes par publication (même règle que le tableau de bord)."""
    g = d.groupby("campagne")
    t = pd.DataFrame({"Publications": g.size()})
    if "canal" in d:
        t["Canal"] = g["canal"].agg(lambda s: ", ".join(sorted(s.dropna().astype(str).unique())))
    for c, nom in VOLUMES.items():
        if c in d and d[c].notna().any():
            t[nom] = g[c].sum()
    for c, nom in TAUX.items():
        if c in d and d[c].notna().any():
            t[nom] = g[c].median()
    ref = d[METRIQUE].median()
    perf = g[METRIQUE].median()
    t["_perf"] = perf
    ecart = (perf / ref - 1) * 100 if ref else perf * np.nan
    t["Écart à la médiane"] = ecart
    t["Statut"] = np.select([ecart >= 10, ecart <= -10], ["🟢 Au-dessus", "🔴 En dessous"], "🟠 Dans la norme")
    t.loc[t["Publications"] < SEUIL, "Statut"] = t["Statut"] + " (fragile)"
    return t.sort_values("_perf", ascending=False)


CAMP = synthese_campagnes(DF)


def tableau_affichage(t):
    v = t.drop(columns=["_perf"]).copy()
    for nom in VOLUMES.values():
        if nom in v:
            v[nom] = v[nom].map(espace)
    for c, nom in TAUX.items():
        if nom in v:
            v[nom] = v[nom].map(lambda x, c=c: "-" if pd.isna(x) else (f"{x:.2f}" if c in ("cpa", "roas") else f"{x * 100:.1f} %"))
    v["Écart à la médiane"] = v["Écart à la médiane"].map(lambda x: "-" if pd.isna(x) else f"{x:+.0f} %")
    cols = ["Statut", "Écart à la médiane"] + [c for c in v.columns if c not in ("Statut", "Écart à la médiane")]
    return v[cols]


def serie_mensuelle_campagnes(d, col, camps, taux):
    d = d[d["campagne"].isin(camps)].dropna(subset=["date", col])
    if d.empty:
        return None
    g = d.set_index("date").groupby("campagne")[col].resample("MS")
    return (g.median() if taux else g.sum()).unstack(0)


def afficher_cartes():
    cartes = ns["CARTES"]
    cols = st.columns(len(cartes))
    for c, (nom, valeur, sous) in zip(cols, cartes):
        c.metric(nom, valeur, help=sous)


def montrer_graphe(nom):
    """Graphique interactif : survol = détail, molette = zoom (tendance), clic sur la légende = mise en avant."""
    est_taux, comp = ns["EST_TAUX"], ns["COMPORTEMENT"]
    ch = {
        "tendance": lambda: gr.tendance(DF, METRIQUE, NOM_M, est_taux),
        "canal": lambda: gr.par_groupe(comp["canal"], "canal", NOM_M, est_taux, f"{NOM_M} médian par canal") if "canal" in comp else None,
        "benchmark": lambda: gr.benchmark(ns["BENCH"], NOM_M, est_taux),
        "creneaux": lambda: gr.creneaux(DF, METRIQUE, NOM_M, est_taux, ORDRE_JOURS),
        "cout": lambda: gr.cout_performance(DF, METRIQUE, NOM_M, est_taux),
        "sentiment": lambda: gr.sentiment(ns["SENT"]),
    }[nom]()
    if ch is None:
        return False
    st.altair_chart(ch, width="stretch")
    return True


# ------------------------------------------------------------------ textes de l'assistant (règles explicables, sans IA générative)
def periode():
    if "date" in DF and DF["date"].notna().any():
        return f"du {DF['date'].min():%d/%m/%Y} au {DF['date'].max():%d/%m/%Y}"
    return "sur la période importée"


def tendance_recente():
    if "date" not in DF or DF["date"].notna().sum() < 10:
        return None
    s = DF.dropna(subset=["date", METRIQUE]).set_index("date")[METRIQUE].sort_index()
    fin = s.index.max()
    recent = s[s.index > fin - pd.Timedelta(days=28)]
    avant = s[(s.index <= fin - pd.Timedelta(days=28)) & (s.index > fin - pd.Timedelta(days=56))]
    if len(recent) < 3 or len(avant) < 3 or avant.median() == 0:
        return None
    return (recent.median() / avant.median() - 1) * 100


def points_forts_difficultes():
    forts, faibles = [], []
    if len(CAMP) > 1:
        b, w = CAMP.index[0], CAMP.index[-1]
        forts.append(f"<b>{b}</b> est la campagne la plus performante ({NOM_M.lower()} médian : {fm(CAMP.loc[b, '_perf'])}, {CAMP.loc[b, 'Écart à la médiane']:+.0f} % vs médiane).")
        faibles.append(f"<b>{w}</b> est la campagne la plus faible ({NOM_M.lower()} médian : {fm(CAMP.loc[w, '_perf'])}, {CAMP.loc[w, 'Écart à la médiane']:+.0f} % vs médiane).")
    comp = ns["COMPORTEMENT"]
    if "format" in comp and len(comp["format"]) > 1:
        f = comp["format"]
        forts.append(f"Le format <b>{f.index[0]}</b> obtient les meilleurs résultats ({fm(f.iloc[0]['median'])}).")
        faibles.append(f"Le format <b>{f.index[-1]}</b> est le moins efficace ({fm(f.iloc[-1]['median'])}).")
    if "cpa" in DF and DF["cpa"].notna().any() and "Coût / action (€)" in CAMP:
        cp = CAMP["Coût / action (€)"].dropna().sort_values()
        if len(cp) > 1:
            forts.append(f"Coût par action le plus bas : <b>{cp.index[0]}</b> ({cp.iloc[0]:.2f} €).")
            faibles.append(f"Coût par action le plus élevé : <b>{cp.index[-1]}</b> ({cp.iloc[-1]:.2f} €).")
    tr = tendance_recente()
    if tr is not None:
        (forts if tr >= 0 else faibles).append(f"Sur les 4 dernières semaines, le {NOM_M.lower()} médian est en <b>{'hausse' if tr >= 0 else 'baisse'} de {abs(tr):.0f} %</b> par rapport aux 4 semaines précédentes.")
    if ns["SENT"] is not None:
        neg = ns["SENT"].get("négatif", 0)
        if "ALERTE" in ns["ALERTE_TXT"]:
            faibles.append(f"<b>Hausse des commentaires négatifs</b> ({neg:.0f} % de négatifs au total) : vérifier les faits avant de répondre.")
        else:
            forts.append(f"Climat des commentaires stable ({ns['SENT'].get('positif', 0):.0f} % de positifs).")
    fragiles = CAMP[CAMP["Publications"] < SEUIL]
    if len(fragiles):
        faibles.append(f"{len(fragiles)} campagne(s) ont moins de {SEUIL} publications : résultats à confirmer avant de décider.")
    return forts, faibles


def idees_publications():
    comp = ns["COMPORTEMENT"]
    canal = comp["canal"].index[0] if "canal" in comp else "instagram"
    fmt = comp["format"].index[0] if "format" in comp else "image"
    jour = comp["jour"].index[0] if "jour" in comp else "Mardi"
    heure = int(comp["heure"].index[0]) if "heure" in comp else 18
    ton = ns["P"]["ton"]
    sujet = "le festival" if mode == "demo" else "votre offre"
    return canal, fmt, jour, heure, ton, [
        f"**Accroche « coulisses »** ({fmt} sur {canal}, {jour} {heure} h) : « J-10 ! On vous emmène dans les coulisses de {sujet}. Qui sera là ? » + appel à commenter.",
        f"**Preuve sociale** ({fmt}) : 3 avis ou réactions du public, puis « Rejoignez-les : lien en bio ».",
        f"**Question à la communauté** ({canal}) : « Votre moment préféré de l'an dernier ? » pour relancer l'engagement.",
        f"**Rappel d'action** (la veille au soir) : « Dernières places, réservez avant minuit » : un seul message clair, un seul lien.",
    ]



# ------------------------------------------------------------------ réseaux sociaux (pastilles) et Mia
_SVG = {
    "instagram": '<defs><linearGradient id="ig" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#F9A03F"/><stop offset=".5" stop-color="#DD2A7B"/><stop offset="1" stop-color="#7B3FBF"/></linearGradient></defs><rect width="24" height="24" rx="6" fill="url(#ig)"/><rect x="5.5" y="5.5" width="13" height="13" rx="4" fill="none" stroke="#fff" stroke-width="1.6"/><circle cx="12" cy="12" r="3.2" fill="none" stroke="#fff" stroke-width="1.6"/><circle cx="16.2" cy="7.8" r="1" fill="#fff"/>',
    "tiktok": '<rect width="24" height="24" rx="6" fill="#111"/><path d="M13 5.5v8.2a2.6 2.6 0 1 1-2.6-2.6" fill="none" stroke="#25F4EE" stroke-width="1.8" stroke-linecap="round" transform="translate(-.7 -.4)"/><path d="M13 5.5v8.2a2.6 2.6 0 1 1-2.6-2.6" fill="none" stroke="#FE2C55" stroke-width="1.8" stroke-linecap="round" transform="translate(.7 .4)"/><path d="M13 5.5v8.2a2.6 2.6 0 1 1-2.6-2.6M13 5.5c.3 1.8 1.6 3 3.5 3.1" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>',
    "linkedin": '<rect width="24" height="24" rx="6" fill="#0A66C2"/><text x="12" y="17" font-size="12" font-weight="700" fill="#fff" text-anchor="middle" font-family="Arial">in</text>',
    "facebook": '<rect width="24" height="24" rx="6" fill="#1877F2"/><text x="13.5" y="20" font-size="19" font-weight="700" fill="#fff" text-anchor="middle" font-family="Arial">f</text>',
    "youtube": '<rect width="24" height="24" rx="6" fill="#E62117"/><path d="M9.5 8v8l7-4z" fill="#fff"/>',
    "newsletter": f'<rect width="24" height="24" rx="6" fill="{POSEIDON}"/><rect x="5" y="7" width="14" height="10" rx="2" fill="none" stroke="#fff" stroke-width="1.6"/><path d="M5.5 8.5l6.5 5 6.5-5" fill="none" stroke="#fff" stroke-width="1.6"/>',
}


def pastille(canal, t=26):
    c = str(canal).lower()
    corps = _SVG.get(c) or f'<rect width="24" height="24" rx="6" fill="{GRIS}"/><text x="12" y="16.5" font-size="12" font-weight="700" fill="#fff" text-anchor="middle" font-family="Arial">{c[:1].upper()}</text>'
    return f'<span class="reseau" title="{c.capitalize()}"><svg viewBox="0 0 24 24" width="{t}" height="{t}">{corps}</svg></span>'


def canaux_de(nom):
    return list(DF[DF["campagne"] == nom]["canal"].dropna().astype(str).str.lower().unique())


def statut_cle(statut):
    return "fort" if statut.startswith("🟢") else ("faible" if statut.startswith("🔴") else "moyen")


def ec(x):
    return "n/a" if pd.isna(x) else f"{x:+.0f} %"


def reco_campagne(nom):
    d = DF[DF["campagne"] == nom]
    cle = statut_cle(CAMP.loc[nom, "Statut"])
    fmt_best = None
    if "format" in d and d["format"].notna().any() and d[METRIQUE].notna().any():
        fmt_best = d.groupby("format")[METRIQUE].median().sort_values(ascending=False).index[0]
    prudence = " (peu de publications : à confirmer)" if len(d) < SEUIL else ""
    if cle == "fort":
        return f"Belle dynamique, bravo ! Continuez sur cette lancée{' avec le format ' + str(fmt_best) if fmt_best else ''}{prudence}."
    if cle == "faible":
        return f"Pas de panique, on peut la redresser : essayez{' le format ' + str(fmt_best) + ' et' if fmt_best else ''} un autre créneau{prudence}."
    return f"Résultats corrects. Un test de format ou de créneau peut la faire passer un cap{prudence}."


def humeur():
    if ns["SENT"] is not None and "ALERTE" in ns["ALERTE_TXT"]:
        return "😟"
    return "🤔" if CAMP["Statut"].str.startswith("🔴").any() else "😊"


def alerte_courte():
    m = re.match(r"Négatifs sur 7 jours : (\S+ %) \(semaine précédente : (\S+ %)\)", ns["ALERTE_TXT"])
    if m:
        return f"les commentaires négatifs représentent {m.group(1)} sur 7 jours (contre {m.group(2)} la semaine précédente)."
    return ns["ALERTE_TXT"].split(" ALERTE")[0]


def message_mia():
    """Texte rédigé à partir des vrais chiffres : rien n'est inventé."""
    parts = []
    if len(CAMP) > 1:
        b, w = CAMP.index[0], CAMP.index[-1]
        eb, ew = CAMP.loc[b, "Écart à la médiane"], CAMP.loc[w, "Écart à la médiane"]
        vb, vw = fm(CAMP.loc[b, "_perf"]), fm(CAMP.loc[w, "_perf"])
        if pd.notna(eb) and pd.notna(ew) and eb >= 10 and ew <= -10:
            parts.append(f"Bonne nouvelle : votre campagne <b>{b}</b> performe ({NOM_M.lower()} {vb}, {eb:+.0f} % vs médiane), et je tiens à vous en féliciter. "
                         f"<b>{w}</b> a besoin d'aide ({vw}, {ew:+.0f} %), mais rien d'irrattrapable : j'ai déjà quelques pistes.")
        elif pd.notna(eb) and eb >= 10:
            parts.append(f"Bonne nouvelle : <b>{b}</b> se détache ({NOM_M.lower()} {vb}, {eb:+.0f} % vs médiane) et aucune campagne ne décroche. Belle régularité !")
        elif pd.notna(ew) and ew <= -10:
            parts.append(f"Soyons honnêtes : <b>{w}</b> est en retrait ({NOM_M.lower()} {vw}, {ew:+.0f} % vs médiane). Ce n'est pas une fatalité, regardons ensemble comment la relancer.")
        else:
            parts.append("Vos campagnes avancent de façon homogène : aucune ne décroche, et c'est plutôt rassurant.")
    else:
        parts.append(f"J'ai analysé votre campagne : {NOM_M.lower()} médian de {fm(DF[METRIQUE].median())}.")
    if ns["SENT"] is not None and "ALERTE" in ns["ALERTE_TXT"]:
        parts.append(f"Un point me préoccupe aussi : {alerte_courte()} Je comprends que ce soit inquiétant. Respirez : on vérifie les faits, puis on prépare une réponse, étape par étape.")
    n_f = int((CAMP["Publications"] < SEUIL).sum())
    if n_f:
        parts.append(f"Par honnêteté, {n_f} campagne(s) reposent sur moins de {SEUIL} publications : je reste prudente avant de conclure.")
    return "<br><br>".join(parts)


def carte_mia(texte, mood=None, titre="Mia, votre assistante"):
    st.markdown(f'<div class="mia"><div class="mia-av" style="background-image:url(data:image/jpeg;base64,{MIA_B64})"><span class="mood">{mood or humeur()}</span></div><div><div class="mia-nom">{titre}</div><div class="mia-txt">{texte}</div></div></div>', unsafe_allow_html=True)


def priorites():
    alerte = ns["SENT"] is not None and "ALERTE" in ns["ALERTE_TXT"]
    bas = CAMP[CAMP["Statut"].str.startswith("🔴")]
    haut = CAMP[CAMP["Statut"].str.startswith("🟢")]
    items = []
    if alerte:
        items.append(("À traiter en premier", "faible", f"Attention : {alerte_courte()} Vérifiez les faits avant de répondre : Mia vous aide à préparer la suite."))
    elif len(bas):
        w = bas.index[-1]
        items.append(("À traiter en premier", "faible", f"<b>{w}</b> est en retrait ({fm(bas.loc[w, '_perf'])}). {reco_campagne(w)}"))
    else:
        items.append(("À surveiller", "moyen", "Aucune alerte aujourd'hui. Gardez un œil sur la tendance."))
    if len(haut):
        b = haut.index[0]
        items.append(("À amplifier", "fort", f"<b>{b}</b> performe ({fm(haut.loc[b, '_perf'])}, {ec(haut.loc[b, 'Écart à la médiane'])} vs médiane). {reco_campagne(b)}"))
    else:
        items.append(("À amplifier", "moyen", "Aucune campagne ne se détache encore : testez un nouveau format pour trouver ce qui fonctionne."))
    fr = CAMP[CAMP["Publications"] < SEUIL]
    if len(fr):
        items.append(("À confirmer", "moyen", f"{len(fr)} campagne(s) reposent sur moins de {SEUIL} publications : confirmez avant de déplacer du budget."))
    else:
        items.append(("À confirmer", "moyen", "Validez vos choix par un test A/B avant de déplacer du budget."))
    return items


def carte_campagne_html(nom):
    r = CAMP.loc[nom]
    cle = statut_cle(r["Statut"])
    pas = "".join(pastille(c) for c in canaux_de(nom))
    return (f'<div class="cc {cle}"><div class="cc-t">{pas}<span class="cc-n">{nom}</span></div><span class="statut">{r["Statut"]}</span>'
            f'<div class="cc-v">{fm(r["_perf"])}</div><div class="cc-s">{NOM_M} · {ec(r["Écart à la médiane"])} vs médiane · {int(r["Publications"])} publications</div>'
            f'<div class="cc-r">{reco_campagne(nom)}</div></div>')


res = prev.prevoir_serie(DF, CIBLE, 8)

# ------------------------------------------------------------------ Gemini (facultatif)
# La clé se met dans les « Secrets » de Streamlit Cloud, JAMAIS dans le code :
#   GEMINI_API_KEY = "..."      (et facultatif : GEMINI_MODEL = "...")
# Sans clé, l'assistant reste en mode simulé (réponses construites à partir des chiffres).
LIMITE_QUESTIONS = 15


def secret(nom, defaut=None):
    try:
        return st.secrets.get(nom, defaut)
    except Exception:
        return defaut


CLE_GEMINI = secret("GEMINI_API_KEY")
MODELE_GEMINI = secret("GEMINI_MODEL", "gemini-2.5-flash")


def contexte_ia():
    """Uniquement des chiffres agrégés : aucun fichier brut n'est envoyé."""
    forts, faibles = points_forts_difficultes()
    nettoyer = lambda x: x.replace("<b>", "").replace("</b>", "")
    prevu = ("indisponible : " + res["erreur"]) if "erreur" in res else (
        f"{espace(res['prevision']['prévision'].head(4).sum())} {nom_cible} sur 4 semaines "
        f"(fourchette {espace(res['prevision']['bas'].head(4).sum())} à {espace(res['prevision']['haut'].head(4).sum())}), confiance {res['confiance']}")
    comp = ns["COMPORTEMENT"]
    lignes = [
        f"Données : {'FICTIVES (démo : lancement d’un festival)' if mode == 'demo' else 'réelles importées'}, {periode()}, {len(DF)} publications, {len(CAMP)} campagnes.",
        f"Objectif : {objectif}. Indicateur suivi : {NOM_M}. Profil : {profil} (ton {ns['P']['ton']} ; règle : {ns['P']['regle']}).",
        "Chiffres clés (médianes) : " + " ; ".join(f"{n} = {v}" for n, v, _ in ns["CARTES"]),
        "Tableau des campagnes (CSV) :", tableau_affichage(CAMP).to_csv(),
        "Points forts : " + " | ".join(map(nettoyer, forts)),
        "Difficultés : " + " | ".join(map(nettoyer, faibles)),
        "Recommandations calculées : " + " | ".join(map(nettoyer, ns["recommandations"]())),
        f"Prévision : {prevu}.",
        f"Commentaires : {ns['ALERTE_TXT']}",
    ]
    for c in ("format", "jour", "heure"):
        if c in comp:
            lignes.append(f"Classement par {c} ({NOM_M} médian, nombre de publications) : "
                          + " ; ".join(f"{i} = {fm(r['median'])} (n={int(r['count'])})" for i, r in comp[c].head(5).iterrows()))
    return "\n".join(lignes)


CONSIGNE = ("Tu es Mia, l'assistante IA de Lumen, une plateforme d'analyse de campagnes de communication. Tu es chaleureuse, bienveillante, empathique et professionnelle : tu vouvoies, tu félicites quand c'est mérité, tu rassures quand un résultat est mauvais. Réponds en français, "
            "de façon courte, claire et concrète, à un professionnel de la communication qui n'est pas statisticien. "
            "Appuie-toi UNIQUEMENT sur les données fournies ; si l'information n'y est pas, dis-le au lieu d'inventer. "
            "Signale quand un résultat repose sur peu de publications. Ne donne jamais d'ordre : propose, l'humain décide.")


def demander_gemini(messages):
    """messages = [(rôle 'user'|'model', texte)]. Retourne (texte, erreur)."""
    import requests
    corps = {
        "system_instruction": {"parts": [{"text": CONSIGNE + "\n\nDONNÉES :\n" + contexte_ia()}]},
        "contents": [{"role": r, "parts": [{"text": t}]} for r, t in messages],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200},
    }
    try:
        rep = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODELE_GEMINI}:generateContent",
                            headers={"x-goog-api-key": CLE_GEMINI, "Content-Type": "application/json"}, json=corps, timeout=60)
        data = rep.json()
        if rep.status_code != 200:
            return None, data.get("error", {}).get("message", f"erreur {rep.status_code}")
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip(), None
    except Exception as e:
        return None, f"{type(e).__name__} : {e}"


def quota_ok():
    n = st.session_state.get("nb_questions", 0)
    if n >= LIMITE_QUESTIONS:
        st.warning(f"Limite de {LIMITE_QUESTIONS} questions atteinte pour cette visite (protection de la clé). Rechargez la page pour recommencer.")
        return False
    st.session_state["nb_questions"] = n + 1
    return True

# ------------------------------------------------------------------ chat flottant avec Mia (bas à gauche, sur toutes les pages)
SUGGESTIONS = ["Quelle campagne fonctionne le mieux ?", "Quelle campagne pose problème ?", "Quand dois-je publier ?",
               "Où mettre mon budget ?", "Mon public est-il satisfait ?", "Que va-t-il se passer ?"]


def _prevision_texte():
    if "erreur" in res:
        return "Je ne peux pas prévoir honnêtement : " + res["erreur"]
    pr = res["prevision"]
    return (f"D'après votre historique, je m'attends à environ <b>{espace(pr['prévision'].head(4).sum())} {nom_cible}</b> sur les 4 prochaines semaines "
            f"(fourchette {espace(pr['bas'].head(4).sum())} à {espace(pr['haut'].head(4).sum())}). Confiance {res['confiance']} : c'est une estimation, pas une promesse.")


def reponse_regles(q):
    """Réponses de Mia construites à partir de vos chiffres (sans IA générative). Rien n'est inventé."""
    t = q.lower()
    forts, faibles = points_forts_difficultes()
    _, fmt_i, jour_i, heure_i, _, _ = idees_publications()
    has = lambda *mots: any(m in t for m in mots)
    if has("bonjour", "salut", "coucou", "hello"):
        return "Bonjour ! Ravie de vous retrouver. Que voulez-vous savoir sur vos campagnes ?"
    if has("merci"):
        return "Avec grand plaisir ! Je suis là dès que vous avez besoin de moi."
    if has("qui es", "qui êtes", "ton nom", "votre nom"):
        return "Je suis Mia, l'assistante IA de Lumen. Je lis vos chiffres, je vous explique et je vous propose des pistes : c'est toujours vous qui décidez."
    if has("publier", "poster", "créneau", "heure", "quand", "jour"):
        return f"D'après vos données, le meilleur moment observé est le <b>{jour_i} vers {heure_i} h</b>, en format <b>{fmt_i}</b>. Attention : ce créneau repose parfois sur peu de publications, testez-le avant de vous y fier."
    if has("budget", "coût", "cout", "cpa", "roas", "argent", "dépens", "investir"):
        return next((r.replace("<b>", "").replace("</b>", "") for r in ns["recommandations"]() if "arbitrer" in r or "Coût" in r), "Je n'ai pas de données de coût dans vos fichiers : ajoutez une colonne « budget » pour que je vous conseille.")
    if has("prévi", "prevo", "futur", "prochain", "semaine", "objectif", "avenir"):
        return _prevision_texte()
    if has("commentaire", "public", "avis", "satisf", "réputation", "reputation", "négatif", "negatif"):
        return ns["ALERTE_TXT"] if ns["SENT"] is not None else "Je n'ai reçu aucun commentaire à analyser. Importez un CSV de commentaires (menu de gauche) et je vous dirai comment réagit votre public."
    if has("format", "contenu", "idée", "idee", "texte", "rédig", "post"):
        return f"Le format qui fonctionne le mieux chez vous est <b>{fmt_i}</b>. Dans « Assistant IA > Améliorer contenus et canaux », je vous propose aussi des idées de publications."
    if has("meilleur", "mieux", "performe", "réussi", "reussi", "fort", "bravo", "bien"):
        return forts[0] if forts else "Je n'ai pas assez de campagnes pour en désigner une."
    if has("problème", "probleme", "faible", "pire", "difficult", "aide", "redress", "mauvais", "inquiet"):
        return (faibles[0] + " Pas de panique : l'onglet Campagnes détaille les pistes.") if faibles else "Je ne vois aucune difficulté nette pour le moment, bonne nouvelle."
    for nom in CAMP.index:
        if nom.lower() in t or any(c in t for c in canaux_de(nom)):
            r = CAMP.loc[nom]
            return (f"<b>{nom}</b> : {NOM_M.lower()} médian {fm(r['_perf'])} ({ec(r['Écart à la médiane'])} vs médiane, {int(r['Publications'])} publications). Statut : {r['Statut']}. {reco_campagne(nom)}")
    return "Je ne suis pas sûre de bien comprendre. Essayez par exemple : « Quelle campagne pose problème ? », « Quand publier ? » ou le nom d'un réseau (TikTok, Instagram…). Avec une clé Gemini, je pourrais répondre à des questions plus libres."


def envoyer(question):
    question = (question or "").strip()
    if not question:
        return
    h = st.session_state.setdefault("chat_mia", [])
    h.append(("user", question))
    rep = None
    if CLE_GEMINI and st.session_state.get("nb_questions", 0) < LIMITE_QUESTIONS:
        st.session_state["nb_questions"] = st.session_state.get("nb_questions", 0) + 1
        rep, _ = demander_gemini([(r, t) for r, t in h[-7:]])
    h.append(("model", rep or reponse_regles(question)))


def vider_chat():
    st.session_state["chat_mia"] = []


def chat_flottant():
    h = st.session_state.get("chat_mia", [])
    with st.container(key="mia_chat"):
        with st.popover("Discuter avec Mia"):
            st.markdown(f'<div class="mia-nom">Mia, votre assistante {humeur()}</div>', unsafe_allow_html=True)
            boite = st.container(height=330, border=False)
            with boite:
                with st.chat_message("assistant", avatar=str(MIA_IMG) if MIA_B64 else humeur()):
                    st.markdown("Bonjour, c'est Mia ! Posez-moi une question sur vos campagnes, ou choisissez une idée ci-dessous."
                                + ("" if mode == "import" else " (Je réponds ici avec les données fictives de la démo.)"))
                for r, t in h[-8:]:
                    with st.chat_message("user" if r == "user" else "assistant", avatar=None if r == "user" else (str(MIA_IMG) if MIA_B64 else humeur())):
                        st.markdown(t, unsafe_allow_html=True)
            if len(h) < 2:
                c = st.columns(2)
                for i, sg in enumerate(SUGGESTIONS):
                    c[i % 2].button(sg, key=f"sg_{i}", on_click=envoyer, args=(sg,), width="stretch")
            with st.form("form_mia", clear_on_submit=True, border=False):
                st.text_input("Votre message", key="msg_mia", placeholder="Écrivez à Mia…", label_visibility="collapsed")
                f1, f2 = st.columns([3, 2])
                f1.form_submit_button("Envoyer", on_click=lambda: envoyer(st.session_state.get("msg_mia")), type="primary", width="stretch")
                f2.form_submit_button("Effacer", on_click=vider_chat, width="stretch")
            st.caption("Mia propose, vous décidez." + (" Propulsé par Gemini." if CLE_GEMINI else " Réponses calculées à partir de vos chiffres."))


st.markdown(f"""<style>
.st-key-mia_chat {{position:fixed !important;right:18px;bottom:18px;left:auto !important;z-index:1000;width:auto !important}}
.st-key-mia_chat button {{border-radius:999px !important;background:{FUCHSIA} !important;background-color:{FUCHSIA} !important;border:2px solid #fff !important;padding:6px 20px 6px 8px !important;box-shadow:0 8px 24px rgba(158,44,106,.45) !important}}
.st-key-mia_chat button:hover {{background:#B13580 !important}}
.st-key-mia_chat button p, .st-key-mia_chat button span {{color:#fff !important;font-weight:600}}
.st-key-mia_chat button::before {{content:"";width:38px;height:38px;border-radius:50%;margin-right:10px;border:2px solid #fff;background:url(data:image/jpeg;base64,{MIA_B64}) center/cover}}
div[data-testid="stPopoverBody"] {{width:min(440px,92vw);border-radius:20px}}
section[data-testid="stSidebar"] {{z-index:100 !important}}
</style>""", unsafe_allow_html=True)
chat_flottant()


# ------------------------------------------------------------------ les quatre espaces

# ================================================================== A. TABLEAU DE BORD
if page == "bord":
    titre_page("Tableau de bord", f"{periode()} · {len(CAMP)} campagnes · {len(DF)} publications · indicateur suivi : {NOM_M} (objectif « {objectif} »)")
    if mode == "demo":
        carte_mia("Bonjour, je suis Mia. Pour que j'analyse <b>vos</b> campagnes, importez vos fichiers dans le menu à gauche : sans fichier, je n'ai rien d'honnête à vous dire. "
                  "En attendant, voici une <b>démonstration</b> avec des données fictives (le lancement d'un festival). Voici ce que je vous dirais :<br><br>" + message_mia(),
                  titre="Mia, votre assistante · " + "démo")
    else:
        carte_mia("Bonjour ! J'ai analysé vos fichiers. " + message_mia())
    st.button("Parler à Mia", on_click=aller, args=("mia",), type="primary")

    st.markdown("### Vos 3 priorités")
    cols = st.columns(3)
    for i, (c, (titre, cle, txt)) in enumerate(zip(cols, priorites()), 1):
        c.markdown(f'<div class="prio {cle}"><div class="prio-t"><span class="prio-n">{i}</span>{titre}</div>{txt}</div>', unsafe_allow_html=True)

    st.markdown("### Vos campagnes")
    noms_c = list(CAMP.index)
    for i in range(0, len(noms_c), 3):
        cols = st.columns(3)
        for c, nom in zip(cols, noms_c[i:i + 3]):
            with c:
                st.markdown(carte_campagne_html(nom), unsafe_allow_html=True)
                st.button("Ouvrir la fiche", key=f"fiche_{nom}", on_click=aller, args=("camp", nom))

    st.markdown("### Chiffres clés")
    afficher_cartes()
    st.markdown("### Tendances")
    c1, c2 = st.columns([2, 1])
    with c1:
        if not montrer_graphe("tendance"):
            st.info("Il faut des dates pour afficher la tendance.")
    with c2:
        montrer_graphe("sentiment") or montrer_graphe("creneaux")
    c1, c2 = st.columns([1, 1])
    with c1:
        montrer_graphe("canal")
    with c2:
        montrer_graphe("creneaux") or montrer_graphe("benchmark")

# ================================================================== B. CAMPAGNES
if page == "camp":
    titre_page("Campagnes", "Comparez vos résultats et ouvrez la fiche de chaque campagne.")
    st.caption("Comparez vos campagnes. Chaque campagne est comparée à la médiane de toutes les publications : vert = au-dessus (+10 % ou plus), brun-rouge = en dessous (−10 % ou plus), bleu = dans la norme. « Fragile » = moins de publications que le seuil fixé : à confirmer.")
    choix = st.multiselect("Campagnes à comparer", list(CAMP.index), default=list(CAMP.index))
    if not choix:
        st.info("Sélectionnez au moins une campagne.")
    else:
        t = CAMP.loc[choix]
        st.dataframe(tableau_affichage(t), width="stretch")

        dispo = {**{nom: (c, True) for c, nom in TAUX.items() if nom in t and c not in ("cpa", "roas")},
                 **{nom: (c, False) for c, nom in VOLUMES.items() if nom in t},
                 **{nom: (c, False) for c, nom in TAUX.items() if nom in t and c in ("cpa", "roas")}}
        noms = list(dispo)
        defaut = next((n for n, (c, _) in dispo.items() if c == METRIQUE), noms[0])
        c1, c2 = st.columns([1, 1])
        ind = c1.selectbox("Indicateur à comparer", noms, index=noms.index(defaut))
        col, est_taux = dispo[ind]
        with c1:
            st.altair_chart(gr.campagnes(t, ind, f"{ind} par campagne (pointillé = médiane)", est_taux), width="stretch")
        with c2:
            mensuel = serie_mensuelle_campagnes(DF, col, choix, est_taux or col in ("cpa", "roas"))
            if mensuel is None or mensuel.empty:
                st.info("Il faut des dates pour suivre l'évolution.")
            else:
                st.altair_chart(gr.evolution_campagnes(mensuel, ind, est_taux), width="stretch")

        st.subheader("Fiche campagne")
        if st.session_state.get("fiche") not in list(CAMP.index):
            st.session_state.pop("fiche", None)
        nom_c = st.selectbox("Ouvrir la fiche de", list(CAMP.index), key="fiche")
        st.markdown("".join(pastille(c, 30) for c in canaux_de(nom_c)) + f' <span class="cc-n">{nom_c}</span> &nbsp;<span class="statut">{CAMP.loc[nom_c, "Statut"]}</span>', unsafe_allow_html=True)
        d = DF[DF["campagne"] == nom_c]
        r = CAMP.loc[nom_c]
        m = st.columns(4)
        m[0].metric("Statut", r["Statut"].split(" (")[0])
        m[1].metric(NOM_M, fm(r["_perf"]), delta=f"{r['Écart à la médiane']:+.0f} % vs médiane")
        m[2].metric("Publications", int(r["Publications"]))
        if "Budget (€)" in r:
            m[3].metric("Budget dépensé", f"{espace(r['Budget (€)'])} €")
        lignes = []
        for c, lib in (("format", "Meilleur format"), ("jour", "Meilleur jour"), ("heure", "Meilleure heure")):
            if c in d and d[METRIQUE].notna().any() and d[c].notna().any():
                tt = d.groupby(c)[METRIQUE].agg(["median", "count"]).sort_values("median", ascending=False)
                v = tt.index[0]
                lignes.append(f"{lib} : <b>{v}{' h' if c == 'heure' else ''}</b> ({fm(tt.iloc[0]['median'])}, {int(tt.iloc[0]['count'])} publication(s))")
        if lignes:
            carte("<br>".join(lignes) + ("<br><i>Moins de " + str(SEUIL) + " publications : à confirmer.</i>" if len(d) < SEUIL else ""), "info")

# ================================================================== C. ASSISTANT IA
if page == "mia":
    titre_page("Assistant IA", "Mia vous explique, anticipe et recommande. Chaque décision reste humaine.")
    carte_mia("Bonjour, c'est Mia ! Je suis là pour vous aider à comprendre vos résultats, sans jargon. Choisissez un volet ci-dessous : "
              "je vous explique chiffres à l'appui, et je vous dis franchement quand je ne suis pas sûre." if mode == "import" else
              "Bonjour, c'est Mia ! Je vous réponds ici à partir des données fictives de la démo. Importez vos fichiers pour que je parle de vos vraies campagnes.")
    s1, s2, s3, s4, s5, s6 = st.tabs(["Comprendre", "Forces et difficultés", "Anticiper", "Recommandations",
                                      "Améliorer contenus et canaux", "Poser une question"])

    # --- 1. comprendre
    with s1:
        st.subheader("Comprendre les performances")
        tr = tendance_recente()
        meilleur = CAMP.index[0] if len(CAMP) else "-"
        faible = CAMP.index[-1] if len(CAMP) else "-"
        resume = (f"{periode().capitalize()}, <b>{len(DF)} publications</b> réparties sur <b>{len(CAMP)} campagnes</b> ont été analysées. "
                  f"Comme l'objectif est « {objectif} », l'IA suit en priorité le <b>{NOM_M.lower()}</b> : sa valeur médiane est de <b>{fm(DF[METRIQUE].median())}</b>. ")
        if len(CAMP) > 1:
            resume += f"La campagne <b>{meilleur}</b> tire les résultats vers le haut, tandis que <b>{faible}</b> est en retrait. "
        if tr is not None:
            resume += f"Sur le dernier mois, la tendance est à la <b>{'hausse' if tr >= 0 else 'baisse'} ({tr:+.0f} %)</b>. "
        if ns["MAPE"] is not None:
            resume += f"Le modèle de prévision se trompe en moyenne de {ns['MAPE']:.0f} % : ses chiffres sont des ordres de grandeur."
        carte(resume, "ia")
        st.caption("Texte rédigé automatiquement à partir de vos chiffres, selon des règles explicables : rien n'est inventé.")
        c1, c2 = st.columns(2)
        with c1:
            montrer_graphe("tendance")
        with c2:
            montrer_graphe("cout") or montrer_graphe("canal")
        with st.expander("Comment l'IA a-t-elle calculé ? (journal détaillé)"):
            st.markdown(f"Formule d'engagement : `{ns['FORMULE']}`")
            st.code(journal or "(rien à afficher)")

    # --- 2. forces et difficultés
    with s2:
        st.subheader("Points forts et difficultés")
        forts, faibles = points_forts_difficultes()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Points forts")
            for f in forts:
                carte(f, "fort")
        with c2:
            st.markdown("#### Difficultés")
            for f in faibles:
                carte(f, "faible")
        c1, c2 = st.columns(2)
        with c1:
            montrer_graphe("benchmark")
        with c2:
            montrer_graphe("sentiment")

    # --- 3. anticiper
    with s3:
        st.subheader("Anticiper les résultats futurs")
        st.caption("Des prévisions simples et explicables : elles prolongent votre passé, elles ne le devinent pas. Si les données sont trop courtes, l'outil refuse plutôt que d'inventer.")
        st.markdown(f"##### A. Évolution prévue ({nom_cible} par semaine)")
        horizon = st.slider("Combien de semaines prévoir ?", 4, 12, 8)
        res = prev.prevoir_serie(DF, CIBLE, horizon)
        if "erreur" in res:
            st.warning(res["erreur"])
        else:
            h, p = res["historique"], res["prevision"]
            st.altair_chart(gr.prevision(h, p, nom_cible), width="stretch")
            niveau = "🟢 correcte" if res["confiance"] == "correcte" else "🟠 fragile (peu de semaines d'historique)"
            st.markdown(f"**Méthode :** {res['methode']}  \n**Confiance :** {niveau} ({res['semaines']} semaines)  \n**À savoir :** {res['limite']}")
            with st.expander("Voir les chiffres"):
                t = p.round(0).astype(int)
                t.index = t.index.strftime("semaine du %d/%m/%Y")
                st.dataframe(t)

        st.markdown("##### B. Mon objectif est-il atteignable ?")
        if "erreur" in res:
            st.info("Cette partie a besoin d'une prévision (voir A).")
        else:
            moyenne = float(res["historique"].tail(4).mean())
            c1, c2 = st.columns(2)
            obj = c1.number_input(f"Objectif en {nom_cible} (total)", min_value=0, value=int(max(moyenne * 4, 1)), step=max(int(moyenne // 10), 1))
            sem = c2.slider("Sur combien de semaines ?", 1, horizon, min(4, horizon))
            r = prev.objectif_atteignable(res, obj, sem)
            {"vert": st.success, "orange": st.warning, "rouge": st.error}[r["niveau"]](f"**{r['verdict']}**")
            m = st.columns(3)
            m[0].metric("Prévu sur la période", espace(r["total"]), help=f"Fourchette : {espace(r['bas'])} à {espace(r['haut'])}")
            m[1].metric("Rythme actuel / semaine", espace(r["rythme_actuel"]), help="Moyenne des 4 dernières semaines")
            m[2].metric("Rythme nécessaire / semaine", espace(r["rythme_necessaire"]),
                        delta=None if r["ecart_pct"] is None else f"{r['ecart_pct']:+.0f} % vs actuel", delta_color="off")
            st.caption(f"Fourchette de la période : {espace(r['bas'])} à {espace(r['haut'])} (estimation prudente). La décision reste humaine.")

        st.markdown("##### C. Simulateur « et si ? » : prévoir une nouvelle publication")
        if ns["MODELE"] is None:
            st.info(f"Pas de simulation possible : {ns['ERR']}")
        else:
            def options(col, defaut):
                if col in DF and DF[col].notna().any():
                    return sorted(DF[col].dropna().astype(str).unique())
                return [defaut]
            c = st.columns(4)
            canal = c[0].selectbox("Canal", options("canal", "instagram"), key="sim_canal")
            fmt_ = c[1].selectbox("Format", options("format", "image"), key="sim_format")
            jour = c[2].selectbox("Jour", ORDRE_JOURS, index=1, key="sim_jour")
            heure = c[3].number_input("Heure", 0, 23, 18, key="sim_heure")
            c = st.columns(4)
            budget = c[0].number_input("Budget (€)", 0, 10**7, 100, step=10, key="sim_budget")
            duree = c[1].number_input("Durée (jours)", 1, 365, 7, key="sim_duree")
            saison = c[2].selectbox("Saison", ["hiver", "printemps", "été", "automne"], index=2, key="sim_saison")
            offre = c[3].selectbox("Offre", ["aucune", "promo", "événement", "nouveauté"], key="sim_offre")
            ligne = {"canal": canal.lower(), "format": fmt_.lower(), "jour": jour, "saison": saison, "type_offre": offre,
                     "budget": budget, "heure": heure, "duree_jours": duree}
            x = pd.DataFrame([{k: ligne.get(k) for k in ns["CATS"] + ns["NUMS"]}])
            pr = float(ns["MODELE"].predict(x)[0])
            m = st.columns(3)
            m[0].metric(f"{nom_cible} prévue", espace(pr))
            m[1].metric("Fourchette basse", espace(pr * ns["BORNES"][0]))
            m[2].metric("Fourchette haute", espace(pr * ns["BORNES"][1]))
            ok = ns["MAPE"] < ns["OBJECTIF_MAPE"]
            (st.success if ok else st.warning)(
                f"Erreur moyenne historique du modèle : {ns['MAPE']:.0f} % (objectif < {ns['OBJECTIF_MAPE']} %). "
                + ("Prévision fiable pour un ordre de grandeur." if ok else "Prévisions indicatives : plus de campagnes passées amélioreront le modèle.")
                + " Estimation, pas promesse.")

    # --- 4. recommandations
    with s4:
        st.subheader("Recommandations")
        st.caption("Cochez les recommandations que vous décidez d'appliquer : l'IA propose, vous validez.")
        recs = ns["recommandations"]()
        valid = 0
        for i, rec in enumerate(recs):
            c1, c2 = st.columns([12, 2])
            with c1:
                carte(rec, "ia")
            with c2:
                st.write("")
                valid += st.checkbox("Je valide", key=f"rec_{i}")
        st.info(f"{valid} recommandation(s) validée(s) sur {len(recs)}.")
        st.markdown("#### Limites et niveau de confiance")
        for l in ns["limites"]():
            carte(l, "vigil")

    # --- 5. améliorer contenus et canaux
    with s5:
        st.subheader("Améliorer les contenus et les canaux")
        st.markdown("##### Quand publier ?")
        cren = prev.meilleurs_creneaux(DF, METRIQUE, SEUIL)
        if not cren:
            st.info("Il faut une colonne de dates (et des heures) pour classer les créneaux.")
        else:
            c1, c2 = st.columns([1, 1])
            with c1:
                montrer_graphe("creneaux")
            with c2:
                if "jour_heure" in cren:
                    t = cren["jour_heure"].head(5).reset_index().rename(columns={"median": f"médiane ({NOM_M})", "count": "publications"})
                    st.markdown("**Top 5 des créneaux jour × heure**")
                    st.dataframe(t.round(4), hide_index=True)
                    top = cren["jour_heure"].iloc[0]
                    j, hr = cren["jour_heure"].index[0]
                    if top["confiance"] == "fragile":
                        st.warning(f"Meilleur créneau observé : {j} à {int(hr)} h, mais seulement {int(top['count'])} publication(s) : à confirmer par un test.")
                    else:
                        st.success(f"Meilleur créneau observé : {j} à {int(hr)} h ({int(top['count'])} publications).")

        st.markdown("##### Quels formats et quels canaux privilégier ?")
        comp = ns["COMPORTEMENT"]
        c1, c2 = st.columns(2)
        for c, col_, titre in ((c1, "format", "Par format"), (c2, "canal", "Par canal")):
            if col_ in comp:
                t = comp[col_].reset_index().rename(columns={"median": f"médiane ({NOM_M})", "count": "publications"})
                c.markdown(f"**{titre}**")
                c.dataframe(t, hide_index=True, width="stretch")

        canal_i, fmt_i, jour_i, heure_i, ton_i, idees = idees_publications()
        if CLE_GEMINI:
            st.markdown("##### Idées de publications " + badge("rédigées par Gemini", "ia"), unsafe_allow_html=True)
            st.caption(f"Gemini s'appuie sur ce qui marche le mieux dans vos données ({fmt_i}, {canal_i}, {jour_i} {heure_i} h) et sur le ton « {ton_i} ». Relisez avant de publier.")
            if st.button("Rédiger 3 publications") and quota_ok():
                with st.spinner("Gemini rédige…"):
                    txt, err = demander_gemini([("user",
                        f"Rédige 3 propositions de publications prêtes à poster pour {canal_i}, au format {fmt_i}, à publier le {jour_i} vers {heure_i} h. "
                        "Pour chacune : un titre court, le texte (avec emojis si adapté au canal), l'appel à l'action, et une phrase qui explique pourquoi, d'après les données.")])
                st.session_state["idees_gemini"] = txt or f"Gemini indisponible ({err}). Voici les modèles prédéfinis ci-dessous."
            if st.session_state.get("idees_gemini"):
                with st.container(border=True):
                    st.markdown(st.session_state["idees_gemini"])
        else:
            st.markdown("##### Idées de publications " + badge("fonction simulée"), unsafe_allow_html=True)
            st.caption(f"Modèles construits à partir de ce qui marche le mieux dans vos données ({fmt_i}, {canal_i}, {jour_i} {heure_i} h) et du ton conseillé « {ton_i} ». "
                       "Avec une clé Gemini, ces textes seraient rédigés par l'IA.")
        if not CLE_GEMINI or not st.session_state.get("idees_gemini"):
            for idee in idees:
                carte(idee.replace("**", "<b>", 1).replace("**", "</b>", 1), "ia")

        st.markdown("##### Test A/B : quelle variante est meilleure ?")
        c = st.columns(4)
        ai = c[0].number_input("A : impressions", 0, 10**9, 0, key="ab_ai")
        ac = c[1].number_input("A : clics", 0, 10**9, 0, key="ab_ac")
        bi = c[2].number_input("B : impressions", 0, 10**9, 0, key="ab_bi")
        bc = c[3].number_input("B : clics", 0, 10**9, 0, key="ab_bc")
        if min(ai, bi) > 0 and ac <= ai and bc <= bi:
            pa, pb = ac / ai, bc / bi
            pp = (ac + bc) / (ai + bi)
            se = np.sqrt(pp * (1 - pp) * (1 / ai + 1 / bi))
            z = (pb - pa) / se if se > 0 else 0
            pv = 2 * (1 - stats.norm.cdf(abs(z)))
            m = st.columns(3)
            m[0].metric("CTR A", f"{pa:.2%}")
            m[1].metric("CTR B", f"{pb:.2%}")
            m[2].metric("p-value", f"{pv:.3f}")
            if pv < .05:
                st.success(f"Différence significative : la variante {'B' if pb > pa else 'A'} est meilleure. À valider par un humain avant de basculer le budget.")
            else:
                st.warning("Différence NON significative : ne concluez pas, poursuivez le test ou augmentez l'échantillon.")
        else:
            st.caption("Exemple : A = 10 000 impressions / 150 clics, B = 10 000 impressions / 210 clics.")

        if ns["SENT"] is not None:
            st.markdown("##### Ce que dit le public (commentaires)")
            if "ALERTE" in ns["ALERTE_TXT"]:
                st.error("" + ns["ALERTE_TXT"])
            else:
                st.info(ns["ALERTE_TXT"])
            with st.expander("Exemples de commentaires négatifs"):
                for v in ns["COMM"][ns["COMM"]["sentiment"] == "négatif"]["commentaire"].head(5):
                    st.markdown(f"- {v}")
            st.caption("Limites : ironie et second degré mal détectés ; les commentateurs ne représentent pas la majorité silencieuse.")

    # --- 6. question (simulé)
    with s6:
        st.subheader("Poser une question à l'assistant")
        if CLE_GEMINI:
            st.markdown(badge("Gemini", "ia") + " &nbsp;Posez votre question librement. Seuls des chiffres agrégés (tableau des campagnes, indicateurs) "
                        "sont envoyés à Gemini, jamais vos fichiers. <b>L'IA propose, vous décidez.</b>", unsafe_allow_html=True)
        else:
            st.markdown(badge("fonction simulée") + " &nbsp;Les réponses sont construites à partir de vos chiffres, sans IA générative. "
                        "Avec une clé Gemini, vous pourriez poser vos propres questions.", unsafe_allow_html=True)
        forts, faibles = points_forts_difficultes()
        canal_i, fmt_i, jour_i, heure_i, ton_i, _ = idees_publications()
        reponses = {
            "Quelle campagne fonctionne le mieux ?": forts[0] if forts else "Pas assez de campagnes pour comparer.",
            "Quelle campagne pose problème ?": faibles[0] if faibles else "Aucune difficulté nette.",
            "Quand dois-je publier ?": f"D'après vos données, le meilleur moment est le <b>{jour_i} vers {heure_i} h</b>, en <b>{fmt_i}</b>. Vérifiez la confiance dans « Améliorer contenus et canaux ».",
            "Où mettre mon budget ?": next((r for r in ns["recommandations"]() if "arbitrer" in r or "Coût" in r), "Pas de données de coût dans vos fichiers."),
            "Que va-t-il se passer dans les prochaines semaines ?": (
                f"Prévision : environ <b>{espace(res['prevision']['prévision'].head(4).sum())} {nom_cible}</b> sur les 4 prochaines semaines "
                f"(fourchette {espace(res['prevision']['bas'].head(4).sum())} à {espace(res['prevision']['haut'].head(4).sum())})."
                if "erreur" not in res else res["erreur"]),
            "Mon public est-il satisfait ?": (ns["ALERTE_TXT"] if ns["SENT"] is not None else "Aucun commentaire importé."),
        }
        if CLE_GEMINI:
            histo = st.session_state.setdefault("chat", [])
            q = st.pills("Exemples de questions", list(reponses), key="pill_q")
            libre = st.chat_input("Votre question (ex. : « Quelle campagne arrêter ? »)")
            question = libre or (q if q and st.session_state.get("pill_deja") != q else None)
            if q:
                st.session_state["pill_deja"] = q
            for r, t in histo:
                with st.chat_message("user" if r == "user" else "assistant", avatar=None if r == "user" else (str(MIA_IMG) if MIA_B64 else humeur())):
                    st.markdown(t)
            if question and quota_ok():
                with st.chat_message("user", avatar=None):
                    st.markdown(question)
                with st.chat_message("assistant", avatar=(str(MIA_IMG) if MIA_B64 else humeur())):
                    with st.spinner("Gemini réfléchit…"):
                        txt, err = demander_gemini(histo[-6:] + [("user", question)])
                    if txt:
                        st.markdown(txt)
                        histo += [("user", question), ("model", txt)]
                    else:
                        st.warning(f"Gemini est indisponible ({err}). Réponse de secours construite à partir de vos chiffres :")
                        st.markdown(reponses.get(question, "Choisissez une des questions proposées."), unsafe_allow_html=True)
            if histo and st.button("Effacer la conversation"):
                st.session_state["chat"] = []
                st.rerun()
        else:
            q = st.radio("Choisissez une question", list(reponses), index=None)
            if q:
                with st.chat_message("user", avatar=None):
                    st.write(q)
                with st.chat_message("assistant", avatar=(str(MIA_IMG) if MIA_B64 else humeur())):
                    st.markdown(reponses[q], unsafe_allow_html=True)
                    st.caption("Réponse fondée sur vos données. À vous de décider.")

# ================================================================== D. RAPPORTS
if page == "rapport":
    titre_page("Rapports", "Une synthèse claire à partager, avec les recommandations de Mia.")
    st.caption(f"{NOM_PLATEFORME} · {periode()} · objectif « {objectif} » · profil « {profil} »"
               + (" · données fictives (démo)" if mode == "demo" else ""))
    afficher_cartes()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 1. Résultats par campagne")
        st.altair_chart(gr.campagnes(CAMP, "_perf", f"{NOM_M} médian par campagne", ns["EST_TAUX"]), width="stretch")
    with c2:
        st.markdown("#### 2. Tendance")
        montrer_graphe("tendance")

    forts, faibles = points_forts_difficultes()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 3. Points forts")
        for f in forts[:3]:
            carte(f, "fort")
    with c2:
        st.markdown("#### 4. Points de vigilance")
        for f in faibles[:3]:
            carte(f, "faible")

    st.markdown("#### 5. Recommandations de l'IA")
    for rec in ns["recommandations"]():
        carte(rec, "ia")
    st.markdown("#### 6. Prévision")
    if "erreur" in res:
        st.info(res["erreur"])
    else:
        carte(f"Sur les 4 prochaines semaines : environ <b>{espace(res['prevision']['prévision'].head(4).sum())} {nom_cible}</b> "
              f"(fourchette {espace(res['prevision']['bas'].head(4).sum())} à {espace(res['prevision']['haut'].head(4).sum())}), confiance {res['confiance']}.", "info")
    with st.expander("Limites de l'analyse"):
        for l in ns["limites"]():
            st.markdown("- " + md(l))

    st.divider()
    st.markdown("#### Partager le rapport")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Préparer le rapport complet (HTML)"):
            S = st.session_state
            rg = dict(REGLAGES, SIM_ON="sim_canal" in S and ns["MODELE"] is not None,
                      CANAL_NEW=S.get("sim_canal", "instagram"), FORMAT_NEW=S.get("sim_format", "image"), JOUR_NEW=S.get("sim_jour", "Mardi"),
                      SAISON_NEW=S.get("sim_saison", "été"), OFFRE_NEW=S.get("sim_offre", "aucune"), BUDGET_NEW=S.get("sim_budget", 100),
                      HEURE_NEW=S.get("sim_heure", 18), DUREE_NEW=S.get("sim_duree", 7),
                      A_IMPRESSIONS=S.get("ab_ai", 0), A_CLICS=S.get("ab_ac", 0), B_IMPRESSIONS=S.get("ab_bi", 0), B_CLICS=S.get("ab_bc", 0))
            try:
                ns2, _ = analyser(dict(fichiers), mode == "demo", rg, comm_bytes)
                st.download_button("Télécharger le rapport (HTML, s'ouvre dans un navigateur)", ns2["HTML_DASH"].encode("utf-8"),
                                   file_name="rapport_campagnes.html", mime="text/html")
            except Exception as e:
                st.error(f"Le rapport n'a pas pu être généré : {e}")
        st.caption("Astuce : pour un PDF, ouvrez le rapport HTML puis Imprimer › Enregistrer en PDF.")
    with c2:
        st.download_button("Tableau des campagnes (CSV)", tableau_affichage(CAMP).to_csv().encode("utf-8"),
                           file_name="comparaison_campagnes.csv", mime="text/csv")
        st.download_button("Données centralisées (CSV)", DF.to_csv(index=False).encode("utf-8"),
                           file_name="donnees_centralisees.csv", mime="text/csv")
    with st.expander(f"Voir les données centralisées ({len(DF)} lignes)"):
        st.caption("Les valeurs manquantes sont laissées vides, jamais inventées.")
        st.dataframe(DF)
