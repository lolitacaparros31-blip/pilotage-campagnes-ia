"""Graphiques interactifs (Altair) : survol = détail, molette = zoom, clic sur la légende = mise en avant.

Les graphiques du rapport HTML restent ceux du moteur (images fixes) ; ceux-ci servent à l'écran.
"""
import altair as alt
import numpy as np
import pandas as pd

POSEIDON, EGRET, FUCHSIA = "#123955", "#F3ECE0", "#9E2C6A"
ALL_ABOARD, NEPTUNE, ACACIA, SPICE, GRIS = "#5D9BCB", "#7FBB9E", "#DACD65", "#884332", "#5B6470"
PAL = [ALL_ABOARD, FUCHSIA, NEPTUNE, "#755139", "#D29380", POSEIDON, "#B98391", "#646049"]
STATUTS = alt.Scale(domain=["Au-dessus", "Dans la norme", "En dessous"], range=[NEPTUNE, ALL_ABOARD, SPICE])


def habiller(ch, titre="", hauteur=300):
    return (ch.properties(title=titre, height=hauteur, background="white")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=GRIS, titleColor=GRIS, gridColor="#E8E1D3", domainColor="#D6CEBF", labelFontSize=11)
            .configure_title(color=POSEIDON, anchor="start", fontSize=14)
            .configure_legend(labelColor=POSEIDON, titleColor=POSEIDON, orient="bottom"))


def _fmt(est_taux):
    return ".1%" if est_taux else ",.0f"


def tendance(df, metrique, nom_m, est_taux):
    if "date" not in df or df["date"].notna().sum() <= 5:
        return None
    cols = [c for c in ["date", metrique, "campagne", "canal", "format"] if c in df]
    d = df.dropna(subset=["date", metrique])[cols].sort_values("date").copy()
    d["tendance"] = d[metrique].rolling(7, min_periods=3).median()
    zoom = alt.selection_interval(bind="scales", encodings=["x"])
    base = alt.Chart(d).encode(x=alt.X("date:T", title=None))
    pts = base.mark_circle(size=55, color=FUCHSIA, opacity=.45).encode(
        y=alt.Y(f"{metrique}:Q", title=nom_m, axis=alt.Axis(format=_fmt(est_taux))),
        tooltip=[alt.Tooltip("date:T", title="Date", format="%d/%m/%Y")]
        + [alt.Tooltip(c, title=c.capitalize()) for c in ("campagne", "canal", "format") if c in d]
        + [alt.Tooltip(f"{metrique}:Q", title=nom_m, format=_fmt(est_taux))]).add_params(zoom)
    ligne = base.mark_line(color=POSEIDON, strokeWidth=2.5).encode(
        y=f"tendance:Q", tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y", title="Date"),
                                  alt.Tooltip("tendance:Q", title="Tendance (médiane glissante)", format=_fmt(est_taux))])
    return habiller(pts + ligne, f"{nom_m} dans le temps")


def par_groupe(t, col, nom_m, est_taux, titre):
    """Barres à partir d'un tableau COMPORTEMENT (index = valeur, colonnes median / count / confiance)."""
    d = t.reset_index().rename(columns={t.index.name or "index": "groupe"})
    d["groupe"] = d["groupe"].astype(str)
    ch = alt.Chart(d).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("groupe:N", sort="-y", title=None, axis=alt.Axis(labelAngle=-25)),
        y=alt.Y("median:Q", title=f"{nom_m} médian", axis=alt.Axis(format=_fmt(est_taux))),
        color=alt.Color("groupe:N", scale=alt.Scale(range=PAL), legend=None),
        opacity=alt.condition("datum.confiance == 'correcte'", alt.value(1), alt.value(.55)),
        tooltip=[alt.Tooltip("groupe:N", title=col.capitalize()), alt.Tooltip("median:Q", title=f"{nom_m} médian", format=_fmt(est_taux)),
                 alt.Tooltip("count:Q", title="Publications"), alt.Tooltip("confiance:N", title="Confiance")])
    return habiller(ch, titre)


def benchmark(bench, nom_m, est_taux):
    if bench is None or not len(bench):
        return None
    d = bench.head(10).copy()
    d["segment"] = [f"{c} · {f}" if f != "tous formats" else c for c, f in zip(d["canal"], d["format"])]
    ch = alt.Chart(d).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y("segment:N", sort="-x", title=None),
        x=alt.X("médiane:Q", title=f"{nom_m} médian", axis=alt.Axis(format=_fmt(est_taux))),
        color=alt.Color("confiance:N", title="Confiance", scale=alt.Scale(domain=["correcte", "fragile"], range=[FUCHSIA, "#D9B2C4"])),
        tooltip=[alt.Tooltip("segment:N", title="Segment"), alt.Tooltip("médiane:Q", title="Médiane", format=_fmt(est_taux)),
                 alt.Tooltip("n:Q", title="Publications"), alt.Tooltip("confiance:N", title="Confiance")])
    return habiller(ch, "Meilleurs segments canal × format")


def creneaux(df, metrique, nom_m, est_taux, ordre_jours):
    if "jour" not in df or "heure" not in df:
        return None
    d = df.dropna(subset=["jour", "heure", metrique]).groupby(["jour", "heure"])[metrique].agg(["median", "count"]).reset_index()
    if d["jour"].nunique() < 2 or d["heure"].nunique() < 2:
        return None
    d["heure"] = d["heure"].astype(int).astype(str) + " h"
    heures = sorted(d["heure"].unique(), key=lambda h: int(h.split()[0]))
    ch = alt.Chart(d).mark_rect(cornerRadius=3).encode(
        x=alt.X("heure:O", sort=heures, title=None), y=alt.Y("jour:O", sort=[j for j in ordre_jours if j in set(d["jour"])], title=None, axis=alt.Axis(labelOverlap=False)),
        color=alt.Color("median:Q", title=nom_m, scale=alt.Scale(range=[EGRET, "#D29380", FUCHSIA]), legend=alt.Legend(format=_fmt(est_taux))),
        tooltip=[alt.Tooltip("jour:N", title="Jour"), alt.Tooltip("heure:N", title="Heure"),
                 alt.Tooltip("median:Q", title=f"{nom_m} médian", format=_fmt(est_taux)), alt.Tooltip("count:Q", title="Publications")])
    return habiller(ch, "Meilleurs créneaux : jour × heure (plus foncé = mieux)", hauteur=320)


def cout_performance(df, metrique, nom_m, est_taux):
    if "cpa" not in df or not df["cpa"].notna().any():
        return None
    g = df.groupby("canal").agg(cpa=("cpa", "median"), perf=(metrique, "median"), n=("canal", "size")).dropna().reset_index()
    if len(g) < 2:
        return None
    ch = alt.Chart(g).mark_circle(opacity=.85, stroke="white").encode(
        x=alt.X("cpa:Q", title="Coût par action en € (plus bas = mieux)", scale=alt.Scale(zero=False)),
        y=alt.Y("perf:Q", title=nom_m, axis=alt.Axis(format=_fmt(est_taux)), scale=alt.Scale(zero=False)),
        size=alt.Size("n:Q", legend=None, scale=alt.Scale(range=[200, 900])),
        color=alt.Color("canal:N", scale=alt.Scale(range=PAL), title="Canal"),
        tooltip=[alt.Tooltip("canal:N", title="Canal"), alt.Tooltip("cpa:Q", title="Coût / action (€)", format=".2f"),
                 alt.Tooltip("perf:Q", title=nom_m, format=_fmt(est_taux)), alt.Tooltip("n:Q", title="Publications")])
    return habiller(ch, "Coût et performance par canal (en haut à gauche = idéal)")


def sentiment(sent):
    if sent is None:
        return None
    d = pd.DataFrame({"sentiment": sent.index, "part": sent.values / 100})
    ch = alt.Chart(d).mark_arc(innerRadius=70, stroke="white").encode(
        theta="part:Q",
        color=alt.Color("sentiment:N", title="Sentiment", scale=alt.Scale(domain=["positif", "neutre", "négatif"], range=[NEPTUNE, "#CFC6B6", SPICE])),
        tooltip=[alt.Tooltip("sentiment:N", title="Sentiment"), alt.Tooltip("part:Q", title="Part des commentaires", format=".0%")])
    return habiller(ch, "Sentiment des commentaires")


def campagnes(t, col, titre, est_taux):
    d = t[[col, "Publications", "Statut"]].dropna().reset_index().rename(columns={col: "valeur", t.index.name or "index": "campagne"})
    d["statut"] = d["Statut"].str.replace(r"^\S+\s|\s\(fragile\)$", "", regex=True)
    d["fragile"] = np.where(d["Statut"].str.contains("fragile"), "oui (à confirmer)", "non")
    fmt = ".1%" if est_taux else (",.2f" if d["valeur"].abs().max() < 100 else ",.0f")
    barres = alt.Chart(d).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y("campagne:N", sort="-x", title=None),
        x=alt.X("valeur:Q", title=None, axis=alt.Axis(format=fmt)),
        color=alt.Color("statut:N", scale=STATUTS, title="Statut"),
        tooltip=[alt.Tooltip("campagne:N", title="Campagne"), alt.Tooltip("valeur:Q", title=titre.split(" par ")[0], format=fmt),
                 alt.Tooltip("Publications:Q"), alt.Tooltip("statut:N", title="Statut"), alt.Tooltip("fragile:N", title="Échantillon fragile")])
    med = alt.Chart(pd.DataFrame({"m": [d["valeur"].median()]})).mark_rule(color=GRIS, strokeDash=[4, 4]).encode(
        x="m:Q", tooltip=[alt.Tooltip("m:Q", title="Médiane des campagnes", format=fmt)])
    return habiller(barres + med, titre, hauteur=max(160, 38 * len(d)))


def evolution_campagnes(mensuel, nom, est_taux):
    d = mensuel.reset_index().melt(id_vars="date", var_name="campagne", value_name="valeur").dropna()
    choix = alt.selection_point(fields=["campagne"], bind="legend")
    ch = alt.Chart(d).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%b %Y")),
        y=alt.Y("valeur:Q", title=nom, axis=alt.Axis(format=_fmt(est_taux))),
        color=alt.Color("campagne:N", scale=alt.Scale(range=PAL), title="Campagne (cliquer pour isoler)"),
        opacity=alt.condition(choix, alt.value(1), alt.value(.12)),
        tooltip=[alt.Tooltip("campagne:N", title="Campagne"), alt.Tooltip("date:T", title="Mois", format="%B %Y"),
                 alt.Tooltip("valeur:Q", title=nom, format=_fmt(est_taux) if est_taux else ",.2f")]).add_params(choix)
    return habiller(ch, f"Évolution par mois : {nom}", hauteur=330)


def prevision(hist, prev_, nom):
    h = pd.DataFrame({"date": hist.index, "valeur": hist.values, "type": "Historique"})
    p = prev_.reset_index().rename(columns={prev_.index.name or "index": "date", "prévision": "valeur"})
    p["type"] = "Prévision"
    couleurs = alt.Scale(domain=["Historique", "Prévision"], range=[POSEIDON, ALL_ABOARD])
    bande = alt.Chart(p).mark_area(opacity=.22, color=ALL_ABOARD).encode(
        x="date:T", y="bas:Q", y2="haut:Q",
        tooltip=[alt.Tooltip("date:T", title="Semaine du", format="%d/%m/%Y"), alt.Tooltip("bas:Q", title="Bas (80 %)", format=",.0f"),
                 alt.Tooltip("haut:Q", title="Haut (80 %)", format=",.0f")])
    lignes = alt.Chart(pd.concat([h, p[["date", "valeur", "type"]]])).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("date:T", title=None), y=alt.Y("valeur:Q", title=f"{nom} par semaine"),
        color=alt.Color("type:N", scale=couleurs, title=None),
        strokeDash=alt.condition("datum.type == 'Prévision'", alt.value([6, 4]), alt.value([1, 0])),
        tooltip=[alt.Tooltip("type:N", title=""), alt.Tooltip("date:T", title="Semaine du", format="%d/%m/%Y"),
                 alt.Tooltip("valeur:Q", title=nom, format=",.0f")])
    return habiller(bande + lignes, "Historique et prévision (zone bleue = fourchette à 80 %)", hauteur=320)
