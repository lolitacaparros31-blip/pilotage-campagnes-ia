"""Plateforme IA de pilotage de campagnes : interface Streamlit.

Lancer en local :  streamlit run app.py
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

ROSE, VIOLET, GRIS = "#E6007E", "#7C3AED", "#6B6780"

st.set_page_config(page_title="Pilotage de campagnes IA", page_icon="📊", layout="wide")
st.markdown(f"""
<style>
.hero {{background:linear-gradient(120deg,{ROSE},{VIOLET});color:#fff;padding:22px 26px;border-radius:18px;margin-bottom:14px}}
.hero h1 {{margin:0 0 4px;font-size:28px;color:#fff}} .hero p {{margin:0;opacity:.92}}
div[data-testid="stMetric"] {{background:#fff;border-radius:14px;padding:12px 14px;box-shadow:0 3px 12px rgba(124,58,237,.12)}}
div[data-testid="stMetricValue"] {{color:{ROSE}}}
.demo {{display:inline-block;background:#FFF3C4;color:#7A5B00;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:bold}}
</style>
<div class="hero"><h1>📊 Pilotage de campagnes par l'IA</h1>
<p>Importez vos exports, obtenez un tableau de bord, des prévisions et des recommandations. <b>L'IA recommande, l'humain décide.</b></p></div>
""", unsafe_allow_html=True)


def md(texte):
    return texte.replace("<b>", "**").replace("</b>", "**")


def espace(n):
    return f"{n:,.0f}".replace(",", " ")


# ------------------------------------------------------------------ réglages
with st.sidebar:
    st.header("⚙️ Réglages")
    profil = st.selectbox("Sujet de la campagne", list(PROFILS), help="Adapte le ton conseillé et les règles de conformité.")
    objectif = st.selectbox("Objectif principal", ["notoriété", "engagement", "trafic", "conversion", "fidélisation"], index=3)
    base = st.selectbox("Taux d'engagement calculé sur", ["portée", "abonnés", "vues"], help="La portée est conseillée : elle reflète les personnes réellement touchées.")
    nb_abonnes = st.number_input("Nombre d'abonnés (si base = abonnés)", 0, 10**9, 5000, step=100)
    with st.expander("Réglages avancés"):
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


# ------------------------------------------------------------------ import / démo
col_up, col_demo = st.columns([4, 1])
with col_up:
    fichiers_up = st.file_uploader("📂 Importer mes fichiers (CSV ou Excel exportés de vos comptes)",
                                   type=["csv", "xls", "xlsx"], accept_multiple_files=True)
    with st.expander("💬 Ajouter des commentaires (facultatif, CSV avec une colonne de texte)"):
        comm_up = st.file_uploader("Commentaires", type=["csv"], key="comm", label_visibility="collapsed")
with col_demo:
    st.write("")
    st.write("")
    clic_demo = st.button("▶ Voir la démo", use_container_width=True, help="Charge des données fictives pour montrer le résultat.")

fichiers = tuple(sorted((f.name, f.getvalue()) for f in (fichiers_up or [])))
sig = tuple((n, len(c)) for n, c in fichiers)
if clic_demo:
    st.session_state["mode"] = "demo"
elif fichiers and st.session_state.get("sig") != sig:
    st.session_state["mode"] = "import"
st.session_state["sig"] = sig
if not fichiers and st.session_state.get("mode") == "import":
    st.session_state["mode"] = None
mode = st.session_state.get("mode")
comm_bytes = comm_up.getvalue() if comm_up is not None else None

if mode is None:
    st.info("👆 Importez vos fichiers pour commencer, ou cliquez sur **▶ Voir la démo** pour découvrir l'outil avec des données fictives.")
    st.markdown("""
| Colonne attendue | Exemple de noms reconnus |
|---|---|
| **canal** | canal, plateforme, platform, channel |
| **date** | date, published, date_publication |
| **impressions / portée / vues** | impressions, reach, portée, views |
| clics, likes, commentaires, partages | clicks, likes, comments, shares |
| budget, conversions, revenu | spend, purchases, revenue |

Les noms français et anglais des exports courants sont reconnus. Une colonne manquante n'empêche pas l'analyse : l'outil le signale et ne devine jamais.
""")
    st.stop()

try:
    with st.spinner("Analyse en cours…"):
        ns, journal = calculer(fichiers, mode == "demo", tuple(sorted(REGLAGES.items())), comm_bytes)
except Exception as e:
    st.error(f"L'analyse n'a pas pu aboutir : {type(e).__name__} : {e}")
    if not isinstance(e, ValueError):
        st.caption("Copiez ce message et envoyez-le à Claude pour obtenir de l'aide.")
    with st.expander("Détails"):
        st.code(getattr(e, "journal", "") or str(e))
    st.stop()

DF = ns["DF"]
if mode == "demo":
    st.markdown('<span class="demo">Données fictives (démo)</span>', unsafe_allow_html=True)

CIBLE = ns["CIBLE"]
NOMS = {"portee": "portée", "interactions": "interactions", "clics": "clics", "conversions": "conversions", "impressions": "impressions"}
nom_cible = NOMS.get(CIBLE, CIBLE)

tab_vue, tab_prev, tab_sim, tab_comm, tab_rapport = st.tabs(
    ["📊 Vue d'ensemble", "🔮 Prévisions", "🧪 Simulateur et A/B", "💬 Commentaires", "📥 Rapport et données"])

# ------------------------------------------------------------------ vue d'ensemble
with tab_vue:
    cartes = ns["CARTES"]
    cols = st.columns(len(cartes))
    for c, (nom, valeur, sous) in zip(cols, cartes):
        c.metric(nom, valeur, help=sous)
    if ns["SENT"] is not None and "ALERTE" in ns["ALERTE_TXT"]:
        st.error("🚨 " + ns["ALERTE_TXT"])
    g = ns["GRAPHES"]
    for i in range(0, len(g), 2):
        c = st.columns(2)
        for j, (_, _, b64) in enumerate(g[i:i + 2]):
            c[j].image(base64.b64decode(b64))
    st.subheader("Recommandations")
    st.caption("L'IA recommande, l'humain décide.")
    for r in ns["recommandations"]():
        st.markdown("- " + md(r))
    st.subheader("Limites et niveau de confiance")
    for l in ns["limites"]():
        st.markdown("- " + md(l))
    with st.expander("Détails du calcul"):
        st.code(journal or "(rien à afficher)")

# ------------------------------------------------------------------ prévisions
with tab_prev:
    st.caption("Des prévisions simples et explicables : elles prolongent votre passé, elles ne le devinent pas. Si les données sont trop courtes, l'outil refuse plutôt que d'inventer.")
    st.subheader(f"A. Évolution prévue ({nom_cible} par semaine)")
    horizon = st.slider("Combien de semaines prévoir ?", 4, 12, 8)
    res = prev.prevoir_serie(DF, CIBLE, horizon)
    if "erreur" in res:
        st.warning(res["erreur"])
    else:
        h, p = res["historique"], res["prevision"]
        fig, ax = plt.subplots(figsize=(9, 3.6))
        ax.plot(h.index, h.values, color=VIOLET, lw=2.2, label="Historique")
        ax.plot(p.index, p["prévision"], color=ROSE, lw=2.2, ls="--", label="Prévision")
        ax.fill_between(p.index, p["bas"], p["haut"], color=ROSE, alpha=.15, label="Fourchette 80 %")
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(axis="y", color="#EEEAF6")
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

    st.subheader("B. Meilleurs moments pour publier")
    metrique = ns["METRIQUE_PRINCIPALE"]
    cren = prev.meilleurs_creneaux(DF, metrique, ns["SEUIL_ECHANTILLON"])
    if not cren:
        st.info("Il faut une colonne de dates (et des heures) pour classer les créneaux.")
    else:
        cc = st.columns(2)
        for c, col, titre in zip(cc, ("jour", "heure"), ("Par jour", "Par heure")):
            if col in cren:
                t = cren[col].reset_index().rename(columns={"median": f"médiane ({metrique})", "count": "publications"})
                c.markdown(f"**{titre}**")
                c.dataframe(t.head(7).round(4))
        if "jour_heure" in cren:
            t = cren["jour_heure"].head(5).reset_index().rename(columns={"median": f"médiane ({metrique})", "count": "publications"})
            st.markdown("**Top 5 des combinaisons jour × heure**")
            st.dataframe(t.round(4))
            top = cren["jour_heure"].iloc[0]
            j, hr = cren["jour_heure"].index[0]
            if top["confiance"] == "fragile":
                st.warning(f"Meilleur créneau observé : {j} à {int(hr)} h, mais seulement {int(top['count'])} publication(s) : à confirmer par un test avant de s'y fier.")
            else:
                st.success(f"Meilleur créneau observé : {j} à {int(hr)} h ({int(top['count'])} publications).")

    st.subheader("C. Mon objectif est-il atteignable ?")
    if "erreur" in res:
        st.info("Cette partie a besoin d'une prévision (voir A).")
    else:
        moyenne = float(res["historique"].tail(4).mean())
        c1, c2 = st.columns(2)
        obj = c1.number_input(f"Objectif en {nom_cible} (total)", min_value=0, value=int(max(moyenne * 4, 1)), step=max(int(moyenne // 10), 1))
        sem = c2.slider("Sur combien de semaines ?", 1, horizon, min(4, horizon))
        r = prev.objectif_atteignable(res, obj, sem)
        msg = f"**{r['verdict']}**"
        {"vert": st.success, "orange": st.warning, "rouge": st.error}[r["niveau"]](msg)
        m = st.columns(3)
        m[0].metric("Prévu sur la période", espace(r["total"]), help=f"Fourchette : {espace(r['bas'])} à {espace(r['haut'])}")
        m[1].metric("Rythme actuel / semaine", espace(r["rythme_actuel"]), help="Moyenne des 4 dernières semaines")
        m[2].metric("Rythme nécessaire / semaine", espace(r["rythme_necessaire"]),
                    delta=None if r["ecart_pct"] is None else f"{r['ecart_pct']:+.0f} % vs actuel", delta_color="off")
        st.caption(f"Fourchette de la période : {espace(r['bas'])} à {espace(r['haut'])} (bornes additionnées semaine par semaine : estimation prudente). La décision reste humaine.")

# ------------------------------------------------------------------ simulateur et A/B
def options(col, defaut):
    if col in DF and DF[col].notna().any():
        return sorted(DF[col].dropna().astype(str).unique())
    return [defaut]


with tab_sim:
    st.subheader("Simulateur « et si ? »")
    if ns["MODELE"] is None:
        st.info(f"Pas de simulation possible : {ns['ERR']}")
    else:
        c = st.columns(4)
        canal = c[0].selectbox("Canal", options("canal", "instagram"), key="sim_canal")
        fmt = c[1].selectbox("Format", options("format", "image"), key="sim_format")
        jour = c[2].selectbox("Jour", ORDRE_JOURS, index=1, key="sim_jour")
        heure = c[3].number_input("Heure", 0, 23, 18, key="sim_heure")
        c = st.columns(4)
        budget = c[0].number_input("Budget (€)", 0, 10**7, 100, step=10, key="sim_budget")
        duree = c[1].number_input("Durée (jours)", 1, 365, 7, key="sim_duree")
        saison = c[2].selectbox("Saison", ["hiver", "printemps", "été", "automne"], index=2, key="sim_saison")
        offre = c[3].selectbox("Offre", ["aucune", "promo", "événement", "nouveauté"], key="sim_offre")
        ligne = {"canal": canal.lower(), "format": fmt.lower(), "jour": jour, "saison": saison, "type_offre": offre,
                 "budget": budget, "heure": heure, "duree_jours": duree}
        x = pd.DataFrame([{k: ligne.get(k) for k in ns["CATS"] + ns["NUMS"]}])
        p = float(ns["MODELE"].predict(x)[0])
        bas, haut = p * ns["BORNES"][0], p * ns["BORNES"][1]
        m = st.columns(3)
        m[0].metric(f"{nom_cible} prévue", espace(p))
        m[1].metric("Fourchette basse", espace(bas))
        m[2].metric("Fourchette haute", espace(haut))
        ok = ns["MAPE"] < ns["OBJECTIF_MAPE"]
        (st.success if ok else st.warning)(
            f"Erreur moyenne historique du modèle : {ns['MAPE']:.0f} % (objectif < {ns['OBJECTIF_MAPE']} %). "
            + ("Prévision fiable pour un ordre de grandeur." if ok else "Prévisions indicatives : plus de campagnes passées amélioreront le modèle.")
            + " Estimation, pas promesse.")
        if canal.lower() not in set(DF["canal"]):
            st.caption(f"Le canal « {canal} » n'existe pas dans vos données : prévision moins fiable.")

    st.subheader("Test A/B : quelle variante est meilleure ?")
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
        st.caption("Saisissez les impressions et clics de vos deux variantes (les clics ne peuvent pas dépasser les impressions).")

# ------------------------------------------------------------------ commentaires
with tab_comm:
    if ns["SENT"] is None:
        st.info("Aucun commentaire analysé. Ajoutez un CSV de commentaires (colonne « commentaire », « text » ou « message », et idéalement « date ») dans le bloc 💬 en haut de page.")
    else:
        st.bar_chart(ns["SENT"])
        if "ALERTE" in ns["ALERTE_TXT"]:
            st.error("🚨 " + ns["ALERTE_TXT"])
        else:
            st.info(ns["ALERTE_TXT"])
        st.markdown("**Exemples de commentaires négatifs**")
        for v in ns["COMM"][ns["COMM"]["sentiment"] == "négatif"]["commentaire"].head(5):
            st.markdown(f"- {v}")
        st.caption("Limites : ironie, jargon local et second degré mal détectés ; les commentateurs ne représentent pas la majorité silencieuse ; en dessous de 30 commentaires, aucune valeur statistique.")

# ------------------------------------------------------------------ rapport
with tab_rapport:
    st.subheader("Rapport HTML")
    st.caption("Le rapport reprend vos réglages, ainsi que la simulation et le test A/B saisis dans l'onglet précédent.")
    if st.button("Préparer le rapport complet"):
        S = st.session_state
        rg = dict(REGLAGES, SIM_ON="sim_canal" in S and ns["MODELE"] is not None,
                  CANAL_NEW=S.get("sim_canal", "instagram"), FORMAT_NEW=S.get("sim_format", "image"), JOUR_NEW=S.get("sim_jour", "Mardi"),
                  SAISON_NEW=S.get("sim_saison", "été"), OFFRE_NEW=S.get("sim_offre", "aucune"), BUDGET_NEW=S.get("sim_budget", 100),
                  HEURE_NEW=S.get("sim_heure", 18), DUREE_NEW=S.get("sim_duree", 7),
                  A_IMPRESSIONS=S.get("ab_ai", 0), A_CLICS=S.get("ab_ac", 0), B_IMPRESSIONS=S.get("ab_bi", 0), B_CLICS=S.get("ab_bc", 0))
        try:
            ns2, _ = analyser(dict(fichiers), mode == "demo", rg, comm_bytes)
            st.download_button("⬇ Télécharger le rapport (HTML)", ns2["HTML_DASH"].encode("utf-8"),
                               file_name="tableau_de_bord_campagne.html", mime="text/html")
        except Exception as e:
            st.error(f"Le rapport n'a pas pu être généré : {e}")
    st.subheader("Données centralisées")
    st.caption(f"{len(DF)} lignes. Les valeurs manquantes sont laissées vides, jamais inventées.")
    st.dataframe(DF)
    st.download_button("⬇ Télécharger les données nettoyées (CSV)", DF.to_csv(index=False).encode("utf-8"),
                       file_name="donnees_centralisees.csv", mime="text/csv")
