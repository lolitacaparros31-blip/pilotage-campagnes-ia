"""Plateforme d'analyse de campagnes générée par IA : interface Streamlit.

Lancer en local :  streamlit run app.py
Quatre espaces : Tableau de bord, Campagnes, Assistant IA, Rapports.
Principe : l'IA recommande, l'humain décide. Aucune donnée n'est inventée.
"""
import base64
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy import stats

from contexte import analyser, PROFILS, ORDRE_JOURS
import prevision as prev

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

NOM_PLATEFORME = "Plateforme d'analyse de campagnes générée par IA"

st.set_page_config(page_title="Analyse de campagnes IA", page_icon="📊", layout="wide")
st.markdown(f"""
<style>
.hero {{background:linear-gradient(120deg,{POSEIDON} 0%,{POSEIDON} 45%,{FUCHSIA} 100%);color:#fff;padding:22px 26px;border-radius:18px;margin-bottom:12px}}
.hero h1 {{margin:0 0 4px;font-size:27px;color:#fff}} .hero p {{margin:0;opacity:.92}}
div[data-testid="stMetric"] {{background:#fff;border-radius:14px;padding:12px 14px;border-top:4px solid {POSEIDON};box-shadow:0 3px 12px rgba(18,57,85,.08)}}
div[data-testid="stMetricValue"] {{color:{POSEIDON}}}
.stTabs button[role="tab"] p {{font-size:17px;font-weight:600}}
.badge {{display:inline-block;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:bold}}
.demo, .simule {{background:#EFE6A8;color:#4A4320}}
.ia {{background:#F1DCE7;color:{FUCHSIA}}}
.carte {{background:#fff;border-radius:14px;padding:14px 16px;margin:6px 0;box-shadow:0 2px 10px rgba(18,57,85,.07)}}
.carte.fort {{border-left:6px solid {NEPTUNE}}} .carte.faible {{border-left:6px solid {SPICE}}}
.carte.ia {{border-left:6px solid {FUCHSIA};color:{POSEIDON}}} .carte.info {{border-left:6px solid {ALL_ABOARD}}}
.carte.vigil {{border-left:6px solid {ACACIA}}}
.carte b {{color:{POSEIDON}}}
</style>
<div class="hero"><h1>📊 {NOM_PLATEFORME}</h1>
<p>Toutes vos campagnes au même endroit : tableau de bord, comparaison, assistant IA et rapports. <b>L'IA recommande, l'humain décide.</b></p></div>
""", unsafe_allow_html=True)


def md(texte):
    return texte.replace("<b>", "**").replace("</b>", "**")


def espace(n):
    return f"{n:,.0f}".replace(",", " ")


def carte(texte, style="info"):
    st.markdown(f'<div class="carte {style}">{texte}</div>', unsafe_allow_html=True)


def badge(texte, style="simule"):
    return f'<span class="badge {style}">{texte}</span>'


def habiller(ax, titre):
    ax.set_title(titre, loc="left", fontsize=12, fontweight="bold", color=POSEIDON, pad=10)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    for s_ in ("left", "bottom"):
        ax.spines[s_].set_color("#D6CEBF")
    ax.tick_params(colors=GRIS)
    ax.grid(axis="y", color="#E8E1D3", lw=.8)
    ax.set_axisbelow(True)


# ------------------------------------------------------------------ réglages et données
with st.sidebar:
    st.header("⚙️ Réglages")
    profil = st.selectbox("Sujet de la campagne", list(PROFILS), help="Adapte le ton conseillé et les règles de conformité.")
    objectif = st.selectbox("Objectif principal", ["notoriété", "engagement", "trafic", "conversion", "fidélisation"], index=3,
                            help="Choisit l'indicateur que l'IA suit en priorité.")
    base = st.selectbox("Taux d'engagement calculé sur", ["portée", "abonnés", "vues"], help="La portée est conseillée : elle reflète les personnes réellement touchées.")
    nb_abonnes = st.number_input("Nombre d'abonnés (si base = abonnés)", 0, 10**9, 5000, step=100)
    with st.expander("Réglages avancés"):
        age = st.number_input("Comparer les publications à l'âge (heures)", 1, 720, 48)
        tol = st.number_input("Tolérance (± heures)", 0, 72, 6)
        seuil = st.number_input("Seuil « échantillon fragile » (publications)", 5, 200, 20)
        mape = st.number_input("Erreur de prévision visée (%)", 5, 100, 20)
        alerte = st.number_input("Alerte si commentaires négatifs ≥ (%)", 10, 90, 40)

    st.divider()
    st.header("📂 Mes données")
    st.caption("Sans fichier, la plateforme affiche une démo avec des données fictives.")
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

if mode == "demo":
    st.markdown(badge("Mode démo : campagnes fictives du « Festival d'été 2026 »", "demo")
                + " &nbsp;Importez vos propres exports dans le menu de gauche (›› en haut à gauche sur mobile).", unsafe_allow_html=True)

with st.expander("👋 Première visite ? Comment utiliser la plateforme", expanded=False):
    st.markdown(f"""
| Espace | À quoi il sert |
|---|---|
| **📊 Tableau de bord** | Voir en 10 secondes si tout va bien : chiffres clés, alertes, tendance. |
| **📣 Campagnes** | Comparer les campagnes entre elles et ouvrir la fiche de l'une d'elles. |
| **🤖 Assistant IA** | Comprendre, repérer forces et difficultés, anticiper, recevoir des recommandations, améliorer contenus et canaux. |
| **📄 Rapports** | Une synthèse visuelle prête à partager ou à télécharger. |

**Code couleur :** {badge("fuchsia = IA", "ia")} · vert = point fort · brun-rouge = difficulté · {badge("jaune = à vérifier ou fonction simulée")}
Les réglages (objectif, sujet) sont dans le menu de gauche : l'IA s'adapte à l'objectif choisi.
""", unsafe_allow_html=True)


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


def graphe_campagnes(t, col, titre, est_taux):
    t = t[[col]].dropna().sort_values(col)
    fig, ax = plt.subplots(figsize=(7, 0.55 * len(t) + 1.2))
    ref = t[col].median()
    couleurs = [NEPTUNE if v >= ref * 1.1 else (SPICE if v <= ref * 0.9 else ALL_ABOARD) for v in t[col]]
    bars = ax.barh(t.index, t[col], color=couleurs, height=.6)
    for b, v in zip(bars, t[col]):
        lab = (f"{v * 100:.1f} %" if est_taux else (f"{v:.2f}" if v < 100 else espace(v)))
        ax.text(v, b.get_y() + b.get_height() / 2, "  " + lab, va="center", fontsize=9, color=POSEIDON)
    ax.axvline(ref, color=GRIS, ls=":", lw=1)
    habiller(ax, titre)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="#E8E1D3")
    fig.tight_layout()
    return fig


def serie_mensuelle_campagnes(d, col, camps, taux):
    d = d[d["campagne"].isin(camps)].dropna(subset=["date", col])
    if d.empty:
        return None
    g = d.set_index("date").groupby("campagne")[col].resample("MS")
    return (g.median() if taux else g.sum()).unstack(0)


def afficher_cartes():
    cartes = ns["CARTES"]
    for i in range(0, len(cartes), 4):
        cols = st.columns(4)
        for c, (nom, valeur, sous) in zip(cols, cartes[i:i + 4]):
            c.metric(nom, valeur, help=sous)


def montrer_graphe(nom):
    for _, n, b64 in ns["GRAPHES"]:
        if n == nom:
            st.image(base64.b64decode(b64), width="stretch")
            return True
    return False


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
        f"**Accroche « coulisses »** ({fmt} sur {canal}, {jour} {heure} h) : « J-10 ! On vous emmène dans les coulisses de {sujet}. Qui sera là ? 👀 » + appel à commenter.",
        f"**Preuve sociale** ({fmt}) : 3 avis ou réactions du public, puis « Rejoignez-les : lien en bio ».",
        f"**Question à la communauté** ({canal}) : « Votre moment préféré de l'an dernier ? » pour relancer l'engagement.",
        f"**Rappel d'action** (la veille au soir) : « Dernières places, réservez avant minuit » : un seul message clair, un seul lien.",
    ]


# ------------------------------------------------------------------ les quatre espaces
tab_bord, tab_camp, tab_ia, tab_rapport = st.tabs(["📊 Tableau de bord", "📣 Campagnes", "🤖 Assistant IA", "📄 Rapports"])

# ================================================================== A. TABLEAU DE BORD
with tab_bord:
    st.caption(f"Activité {periode()} · {len(CAMP)} campagnes · {len(DF)} publications · indicateur suivi : **{NOM_M}** (objectif « {objectif} »)")
    afficher_cartes()

    # alertes
    alertes = []
    if ns["SENT"] is not None and "ALERTE" in ns["ALERTE_TXT"]:
        alertes.append(("faible", "🚨 <b>Alerte e-réputation</b> : " + ns["ALERTE_TXT"]))
    sous = CAMP[CAMP["Statut"].str.startswith("🔴")]
    if len(sous):
        alertes.append(("vigil", f"⚠️ <b>{len(sous)} campagne(s) en dessous de la médiane</b> : {', '.join(sous.index)}. Voir l'onglet Campagnes."))
    tr = tendance_recente()
    if tr is not None and tr <= -10:
        alertes.append(("vigil", f"📉 <b>Tendance en baisse</b> : {NOM_M.lower()} −{abs(tr):.0f} % sur 4 semaines."))
    if alertes:
        st.subheader("Alertes")
        for style, txt in alertes:
            carte(txt, style)

    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.subheader("Où en sont les campagnes ?")
        mini = CAMP[["Statut", "_perf", "Publications"]].copy()
        mini[NOM_M] = mini.pop("_perf").map(fm)
        st.dataframe(mini, width="stretch")
    with c2:
        st.subheader("Tendance")
        if not montrer_graphe("tendance"):
            st.info("Il faut des dates pour afficher la tendance.")

    c1, c2 = st.columns(2)
    with c1:
        montrer_graphe("canal")
    with c2:
        montrer_graphe("sentiment") or montrer_graphe("creneaux")

    st.subheader("🤖 Les 3 points à retenir")
    forts, faibles = points_forts_difficultes()
    for txt in (forts[:1] + faibles[:1] + [r for r in ns["recommandations"]()][:1]):
        carte(txt, "ia")
    st.caption("Détails et explications dans l'onglet 🤖 Assistant IA.")

# ================================================================== B. CAMPAGNES
with tab_camp:
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
            fig = graphe_campagnes(t, ind, f"{ind} par campagne (pointillé = médiane)", est_taux)
            st.pyplot(fig)
            plt.close(fig)
        with c2:
            st.markdown(f"**Évolution par mois : {ind}**")
            mensuel = serie_mensuelle_campagnes(DF, col, choix, est_taux or col in ("cpa", "roas"))
            if mensuel is None or mensuel.empty:
                st.info("Il faut des dates pour suivre l'évolution.")
            else:
                fig, ax = plt.subplots(figsize=(7, 4))
                for i, c in enumerate(mensuel.columns):
                    ax.plot(mensuel.index, mensuel[c], lw=2, color=PAL[i % len(PAL)], label=c, marker="o", ms=3)
                habiller(ax, "")
                ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
                fig.autofmt_xdate()
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        st.subheader("🔎 Fiche campagne")
        nom_c = st.selectbox("Ouvrir la fiche de", choix)
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
with tab_ia:
    st.markdown(badge("🤖 Assistant IA", "ia") + " &nbsp;L'IA analyse vos données, explique et propose. <b>Chaque décision reste humaine.</b>", unsafe_allow_html=True)
    s1, s2, s3, s4, s5, s6 = st.tabs(["💡 Comprendre", "⚖️ Forces et difficultés", "🔮 Anticiper", "✅ Recommandations",
                                      "✍️ Améliorer contenus et canaux", "💬 Poser une question"])

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
            st.markdown("#### ✅ Points forts")
            for f in forts:
                carte(f, "fort")
        with c2:
            st.markdown("#### ⚠️ Difficultés")
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
            fig, ax = plt.subplots(figsize=(9, 3.6))
            ax.plot(h.index, h.values, color=POSEIDON, lw=2.2, label="Historique")
            ax.plot(p.index, p["prévision"], color=ALL_ABOARD, lw=2.4, ls="--", label="Prévision")
            ax.fill_between(p.index, p["bas"], p["haut"], color=ALL_ABOARD, alpha=.2, label="Fourchette 80 %")
            habiller(ax, "")
            ax.legend(frameon=False, loc="upper left")
            fig.autofmt_xdate()
            st.pyplot(fig)
            plt.close(fig)
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

        st.markdown("##### Idées de publications " + badge("fonction simulée"), unsafe_allow_html=True)
        canal_i, fmt_i, jour_i, heure_i, ton_i, idees = idees_publications()
        st.caption(f"Modèles construits à partir de ce qui marche le mieux dans vos données ({fmt_i}, {canal_i}, {jour_i} {heure_i} h) et du ton conseillé « {ton_i} ». "
                   "Dans une version complète, un modèle de langage rédigerait ces textes ; ici ce sont des modèles prédéfinis.")
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
                st.error("🚨 " + ns["ALERTE_TXT"])
            else:
                st.info(ns["ALERTE_TXT"])
            with st.expander("Exemples de commentaires négatifs"):
                for v in ns["COMM"][ns["COMM"]["sentiment"] == "négatif"]["commentaire"].head(5):
                    st.markdown(f"- {v}")
            st.caption("Limites : ironie et second degré mal détectés ; les commentateurs ne représentent pas la majorité silencieuse.")

    # --- 6. question (simulé)
    with s6:
        st.subheader("Poser une question à l'assistant")
        st.markdown(badge("fonction simulée") + " &nbsp;Les réponses sont construites à partir de vos chiffres, sans IA générative. "
                    "Une version complète brancherait ici un modèle de langage.", unsafe_allow_html=True)
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
        q = st.radio("Choisissez une question", list(reponses), index=None)
        if q:
            with st.chat_message("user", avatar="🧑"):
                st.write(q)
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(reponses[q], unsafe_allow_html=True)
                st.caption("Réponse fondée sur vos données. À vous de décider.")

# ================================================================== D. RAPPORTS
with tab_rapport:
    st.subheader("📄 Rapport de synthèse")
    st.caption(f"{NOM_PLATEFORME} · {periode()} · objectif « {objectif} » · profil « {profil} »"
               + (" · données fictives (démo)" if mode == "demo" else ""))
    afficher_cartes()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 1. Résultats par campagne")
        fig = graphe_campagnes(CAMP, "_perf", f"{NOM_M} médian par campagne", ns["EST_TAUX"])
        st.pyplot(fig)
        plt.close(fig)
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
                st.download_button("⬇ Télécharger le rapport (HTML, s'ouvre dans un navigateur)", ns2["HTML_DASH"].encode("utf-8"),
                                   file_name="rapport_campagnes.html", mime="text/html")
            except Exception as e:
                st.error(f"Le rapport n'a pas pu être généré : {e}")
        st.caption("Astuce : pour un PDF, ouvrez le rapport HTML puis Imprimer › Enregistrer en PDF.")
    with c2:
        st.download_button("⬇ Tableau des campagnes (CSV)", tableau_affichage(CAMP).to_csv().encode("utf-8"),
                           file_name="comparaison_campagnes.csv", mime="text/csv")
        st.download_button("⬇ Données centralisées (CSV)", DF.to_csv(index=False).encode("utf-8"),
                           file_name="donnees_centralisees.csv", mime="text/csv")
    with st.expander(f"Voir les données centralisées ({len(DF)} lignes)"):
        st.caption("Les valeurs manquantes sont laissées vides, jamais inventées.")
        st.dataframe(DF)
