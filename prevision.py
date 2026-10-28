"""Prévisions simples et explicables (A, B, C). Aucune donnée n'est inventée.

A. prevoir_serie()      : tendance hebdomadaire + fourchette à 80 %
B. meilleurs_creneaux() : classement jour / heure / combinaison, avec niveau de confiance
C. objectif_atteignable(): un objectif chiffré est-il réaliste au rythme actuel ?
"""
import numpy as np
import pandas as pd
from scipy import stats

SEMAINES_MIN = 8      # en dessous : aucune prévision
SEMAINES_OK = 12      # au-dessus : confiance « correcte »


def serie_hebdo(df, col):
    """Total par semaine de la colonne `col`. Retire la dernière semaine si elle est incomplète."""
    if "date" not in df or col not in df:
        return None, "Il faut une colonne de dates et la colonne à prévoir."
    d = df.dropna(subset=["date", col])
    if len(d) == 0:
        return None, "Aucune ligne avec une date et une valeur."
    s = d.set_index("date")[col].astype(float).resample("W").sum()
    fin_derniere = s.index[-1]
    if d["date"].max() < fin_derniere - pd.Timedelta(days=1) and len(s) > SEMAINES_MIN:
        s = s.iloc[:-1]          # semaine en cours incomplète : elle ferait croire à une baisse
    return s, None


def prevoir_serie(df, col, horizon=8):
    """Prévision hebdomadaire. Retourne un dict, ou {"erreur": ...} si les données sont insuffisantes."""
    s, err = serie_hebdo(df, col)
    if err:
        return {"erreur": err}
    n = len(s)
    if n < SEMAINES_MIN:
        return {"erreur": f"Seulement {n} semaine(s) de données : il en faut au moins {SEMAINES_MIN} pour une prévision honnête. "
                          "Importez un historique plus long."}
    x = np.arange(n, dtype=float)
    y = s.values.astype(float)
    lr = stats.linregress(x, y)
    tendance_significative = lr.pvalue < 0.05
    if tendance_significative:
        fit = lr.intercept + lr.slope * x
        xf = np.arange(n, n + horizon, dtype=float)
        centre = lr.intercept + lr.slope * xf
        ddl = n - 2
        sd = np.sqrt(np.sum((y - fit) ** 2) / ddl)
        sxx = np.sum((x - x.mean()) ** 2)
        marge = stats.t.ppf(0.90, ddl) * sd * np.sqrt(1 + 1 / n + (xf - x.mean()) ** 2 / sxx)
        methode = f"tendance linéaire ({lr.slope:+,.0f} par semaine, significative, p = {lr.pvalue:.3f})".replace(",", " ")
    else:
        m = y.mean()
        sd = y.std(ddof=1)
        centre = np.full(horizon, m)
        marge = np.full(horizon, stats.t.ppf(0.90, n - 1) * sd * np.sqrt(1 + 1 / n))
        methode = f"niveau moyen (aucune tendance significative, p = {lr.pvalue:.2f}) : pas d'invention de hausse ou de baisse"
    centre = np.maximum(centre, 0)
    bas = np.maximum(centre - marge, 0)
    haut = centre + marge
    futur = pd.date_range(s.index[-1] + pd.Timedelta(weeks=1), periods=horizon, freq="W")
    prev = pd.DataFrame({"prévision": centre, "bas": bas, "haut": haut}, index=futur)
    return {
        "historique": s, "prevision": prev, "methode": methode,
        "confiance": "correcte" if n >= SEMAINES_OK else "fragile",
        "semaines": n,
        "limite": "Une prévision prolonge le passé : elle ne voit ni une nouvelle campagne, ni un changement d'algorithme, ni une saison différente.",
    }


def meilleurs_creneaux(df, metrique, seuil):
    """Classe jours, heures et combinaisons jour x heure. `confiance` = fragile sous `seuil` publications (combos : seuil/4)."""
    sortie = {}
    if metrique not in df:
        return sortie
    d = df[df[metrique].notna()]
    for col in ("jour", "heure"):
        if col in d and len(d):
            t = d.groupby(col)[metrique].agg(["median", "count"]).sort_values("median", ascending=False)
            t["confiance"] = np.where(t["count"] < seuil, "fragile", "correcte")
            sortie[col] = t
    if "jour" in d and "heure" in d and len(d):
        t = d.groupby(["jour", "heure"])[metrique].agg(["median", "count"]).sort_values("median", ascending=False)
        petit = max(3, seuil // 4)
        t["confiance"] = np.where(t["count"] < petit, "fragile", "correcte")
        sortie["jour_heure"] = t
    return sortie


def objectif_atteignable(prev, objectif, semaines):
    """Compare un objectif cumulé sur `semaines` à la prévision (bornes additionnées = estimation prudente)."""
    p = prev["prevision"].iloc[:semaines]
    tot, bas, haut = p["prévision"].sum(), p["bas"].sum(), p["haut"].sum()
    if objectif <= bas:
        verdict, niveau = "Très probable : même le scénario bas l'atteint.", "vert"
    elif objectif <= tot:
        verdict, niveau = "Probable : atteint au rythme actuel.", "vert"
    elif objectif <= haut:
        verdict, niveau = "Ambitieux : possible seulement dans le scénario haut. Il faudrait améliorer le rythme.", "orange"
    else:
        verdict, niveau = "Peu réaliste au rythme actuel : au-dessus de la fourchette haute.", "rouge"
    recent = prev["historique"].tail(4).mean()
    return {"verdict": verdict, "niveau": niveau, "total": tot, "bas": bas, "haut": haut,
            "rythme_necessaire": objectif / semaines, "rythme_actuel": recent,
            "ecart_pct": (objectif / semaines / recent - 1) * 100 if recent > 0 else None}
