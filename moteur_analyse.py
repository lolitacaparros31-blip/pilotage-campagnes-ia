
# Dictionnaire de correspondance : ajouter un nom de colonne ici = reconnaître un nouvel export.
ALIAS = {
 "date": ["date","jour_publication","published","date_publication","day","publish_time","date_de_publication"],
 "canal": ["canal","plateforme","platform","channel","réseau","reseau","source"],
 "format": ["format","type_contenu","media_type","type","type_de_publication"],
 "budget": ["budget","dépense","depense","spend","amount_spent","coût","cout","montant_dépensé"],
 "impressions": ["impressions","affichages","impr","impressions_de_la_miniature"],
 "portee": ["portee","portée","reach","couverture"],
 "clics": ["clics","clicks","link_clicks","clics_sur_le_lien"],
 "likes": ["likes","j'aime","reactions","réactions","mentions_j'aime"],
 "commentaires": ["commentaires","comments","comment"],
 "partages": ["partages","shares","share"],
 "vues": ["vues","views","video_views"],
 "conversions": ["conversions","achats","purchases","inscriptions","reservations","réservations","results","résultats"],
 "revenu": ["revenu","revenue","ca","chiffre_affaires","revenus_estimés"],
 "heure": ["heure","hour"],
 "age_releve_h": ["age_releve_h","age_h","âge_relevé_h"],
 "duree_jours": ["duree_jours","durée_jours","duration_days"],
 "saison": ["saison","season"], "type_offre": ["type_offre","offre","offer_type"],
}

def normaliser(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    renomm = {}
    for std, noms in ALIAS.items():
        for n in noms:
            n2 = n.lower().replace(" ", "_")
            if n2 in df.columns and std not in df.columns and n2 not in renomm:
                renomm[n2] = std; break
    return df.rename(columns=renomm)

def valider(df):
    rapport = []
    n0 = len(df)
    df = df.drop_duplicates()
    if len(df) < n0: rapport.append(f"{n0-len(df)} doublon(s) supprimé(s)")
    if "date" in df:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_convert(None)
        bad = int(df["date"].isna().sum())
        if bad: rapport.append(f"{bad} date(s) illisible(s)")
        df["jour"] = df["date"].dt.day_name().map(JOURS)
        if "heure" not in df: df["heure"] = df["date"].dt.hour
    for c in ["budget","impressions","portee","clics","likes","commentaires","partages","vues","conversions","revenu"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            m = int(df[c].isna().sum())
            if m: rapport.append(f"{m} valeur(s) manquante(s) dans {c} (laissées vides, jamais inventées)")
    for c in ["canal","format"]:
        if c in df: df[c] = df[c].astype(str).str.strip().str.lower()
    if "canal" not in df:
        rapport.append("Colonne « canal » absente : tout est rangé dans « non précisé ».")
        df["canal"] = "non précisé"
    if "impressions" not in df and "portee" not in df and "vues" not in df:
        rapport.append("ATTENTION : ni impressions, ni portée, ni vues : les taux ne pourront pas être calculés.")
    if "age_releve_h" not in df:
        rapport.append("Colonne age_releve_h absente : comparaison à âge égal impossible (benchmark moins fiable).")
    return df, rapport

def make_demo(n=90, seed=7):
    rng = np.random.default_rng(seed)
    canaux = ["instagram","tiktok","linkedin","facebook","youtube","newsletter"]
    formats = ["image","vidéo courte","carrousel","texte","vidéo longue"]
    d = pd.DataFrame({
        "id": range(1, n+1),
        "date": pd.date_range("2026-01-05", periods=n, freq="2D"),
        "canal": rng.choice(canaux, n), "format": rng.choice(formats, n),
        "heure": rng.choice([7,9,12,18,20,22], n),
        "saison": rng.choice(["hiver","printemps","été","automne"], n),
        "type_offre": rng.choice(["aucune","promo","événement","nouveauté"], n),
        "budget": rng.integers(0, 600, n).astype(float),
        "duree_jours": rng.integers(1, 15, n),
        "age_releve_h": rng.choice([24,48,48,48,72], n),
    })
    d["jour"] = d["date"].dt.day_name().map(JOURS)
    base = 1500 + d["budget"]*18 + np.where(d["canal"].isin(["tiktok","instagram"]), 4000, 0)
    d["impressions"] = (base * rng.uniform(0.6, 1.5, n)).astype(int)
    d["portee"] = (d["impressions"] * rng.uniform(0.55, 0.85, n)).astype(int)
    ctr = rng.uniform(0.004, 0.03, n) * np.where(d["format"].isin(["vidéo courte","carrousel"]), 1.3, 1.0)
    d["clics"] = (d["impressions"] * ctr).astype(int)
    d["likes"] = (d["portee"] * rng.uniform(0.01, 0.06, n)).astype(int)
    d["commentaires"] = (d["likes"] * rng.uniform(0.03, 0.15, n)).astype(int)
    d["partages"] = (d["likes"] * rng.uniform(0.02, 0.2, n)).astype(int)
    d["vues"] = (d["impressions"] * rng.uniform(0.2, 0.6, n)).astype(int)
    d["conversions"] = (d["clics"] * rng.uniform(0.01, 0.08, n)).astype(int)
    d["revenu"] = d["conversions"] * rng.uniform(15, 60, n)
    return d

if DEMO_MODE:
    brut = make_demo()
else:
    parts = []
    for nom, contenu in FICHIERS.items():
        f = io.BytesIO(contenu)
        try:
            t = pd.read_excel(f) if nom.lower().endswith(("xls","xlsx")) else pd.read_csv(f, sep=None, engine="python")
        except Exception as e:
            print(f"Fichier illisible : {nom} ({e})"); continue
        t["source_fichier"] = nom
        parts.append(normaliser(t))
    if not parts:
        raise ValueError("Aucun fichier lisible. Importez un export CSV ou Excel.")
    brut = pd.concat(parts, ignore_index=True)
if brut.shape[1] < 2 or len(brut) == 0:
    raise ValueError("Le fichier est vide ou illisible. Exportez-le en CSV ou Excel depuis votre plateforme et réessayez.")
DF, RAPPORT_IMPORT = valider(brut)
print(f"{len(DF)} lignes centralisées.")
print("Colonnes reconnues :", [c for c in DF.columns if c in ALIAS])
for r in RAPPORT_IMPORT: print(" -", r)


#@title Calcul des KPI
def sdiv(a, b):
    b = pd.Series(b, index=a.index) if not isinstance(b, pd.Series) else b
    return (a / b.where(b > 0))

def kpis(d):
    d = d.copy()
    g = lambda c: d[c].astype(float) if c in d else pd.Series(np.nan, index=d.index)
    d["ctr"] = sdiv(g("clics"), g("impressions"))
    d["cpc"] = sdiv(g("budget"), g("clics"))
    d["cpm"] = sdiv(g("budget"), g("impressions")) * 1000
    d["cpa"] = sdiv(g("budget"), g("conversions"))
    d["roas"] = sdiv(g("revenu"), g("budget"))
    d["taux_conversion"] = sdiv(g("conversions"), g("clics"))
    inter = g("likes").fillna(0) + g("commentaires").fillna(0) + g("partages").fillna(0)
    base = {"portée": g("portee"), "abonnés": pd.Series(float(NB_ABONNES), index=d.index), "vues": g("vues")}[BASE_ENGAGEMENT]
    d["interactions"] = inter
    d["taux_engagement"] = sdiv(inter, base)
    return d

DF = kpis(DF)
FORMULE = f"taux d'engagement = (likes + commentaires + partages) / {BASE_ENGAGEMENT}"
print("Formule utilisée :", FORMULE)
cols = [c for c in ["ctr","cpc","cpm","cpa","roas","taux_conversion","taux_engagement"] if DF[c].notna().any()]
DF[cols].describe().loc[["count","mean","50%"]].round(4)

#@title Benchmark par segment et à âge égal
def benchmark(d, metrique, canal=None, format_=None, age_h=None):
    s = d.copy()
    notes = []
    if canal and "canal" in s: s = s[s["canal"] == canal]
    if format_ and "format" in s: s = s[s["format"] == format_]
    if age_h is not None and "age_releve_h" in s and s["age_releve_h"].notna().any():
        s = s[(s["age_releve_h"] - age_h).abs() <= TOLERANCE_AGE_H]
    elif age_h is not None:
        notes.append("âge de relevé inconnu : comparaison à âge égal impossible")
    s = s[s[metrique].notna()]
    n = len(s)
    if n < SEUIL_ECHANTILLON:
        notes.append(f"échantillon fragile ({n} publications < {SEUIL_ECHANTILLON})")
    med = s[metrique].median() if n else np.nan
    return s, med, n, notes

def rang(valeur, serie):
    serie = serie.dropna()
    if len(serie) == 0 or pd.isna(valeur): return None
    return int((serie < valeur).sum()), len(serie)

METRIQUE_PRINCIPALE = {"notoriété":"portee","engagement":"taux_engagement","trafic":"ctr","conversion":"taux_conversion","fidélisation":"taux_engagement"}[OBJECTIF]
if METRIQUE_PRINCIPALE not in DF or DF[METRIQUE_PRINCIPALE].notna().sum() == 0:
    for alt in ["ctr","taux_engagement","impressions","portee","vues"]:
        if alt in DF and DF[alt].notna().sum() > 0:
            print(f"Indicateur « {METRIQUE_PRINCIPALE} » indisponible dans vos données : remplacé par « {alt} ».")
            METRIQUE_PRINCIPALE = alt; break
    else:
        raise ValueError("Aucun indicateur calculable : il faut au moins impressions, portée ou vues.")

lignes = []
segs = DF.groupby(["canal","format"]) if "format" in DF else DF.groupby(["canal"])
for key, grp in segs:
    key = key if isinstance(key, tuple) else (key,)
    fmt = key[1] if len(key) > 1 else None
    s, med, n, notes = benchmark(DF, METRIQUE_PRINCIPALE, key[0], fmt, AGE_COMPARAISON_H)
    niveau = "canal + format"
    if n < SEUIL_ECHANTILLON and fmt is not None:
        s2, med2, n2, _ = benchmark(DF, METRIQUE_PRINCIPALE, key[0], None, AGE_COMPARAISON_H)
        if n2 > n: s, med, n, niveau = s2, med2, n2, "canal seul (repli)"
    if n == 0: continue
    lignes.append({"canal": key[0], "format": "tous formats" if niveau.startswith("canal seul") else (fmt or "-"),
                   "niveau": niveau, "n": n, "médiane": round(med, 4),
                   "confiance": "fragile" if n < SEUIL_ECHANTILLON else "correcte"})
BENCH = pd.DataFrame(lignes).drop_duplicates(["canal","format","niveau"]).sort_values("médiane", ascending=False).reset_index(drop=True)
print("Indicateur :", METRIQUE_PRINCIPALE, "| comparaison à", AGE_COMPARAISON_H, "h (+/-", TOLERANCE_AGE_H, "h)")
print(f"{(BENCH['confiance']=='fragile').sum()} segment(s) sur {len(BENCH)} restent fragiles (moins de {SEUIL_ECHANTILLON} publications) : à lire comme indicatifs.")
BENCH.head(15)

#@title Classement de chaque publication dans son segment (rang)
def classer(d):
    out = []
    for _, r in d.iterrows():
        if pd.isna(r.get(METRIQUE_PRINCIPALE)): continue
        s, med, n, notes = benchmark(d, METRIQUE_PRINCIPALE, r.get("canal"), r.get("format"), r.get("age_releve_h", AGE_COMPARAISON_H))
        rk = rang(r[METRIQUE_PRINCIPALE], s[METRIQUE_PRINCIPALE])
        out.append({"id": r.get("id", _), "canal": r.get("canal"), "format": r.get("format"),
                    "valeur": round(r[METRIQUE_PRINCIPALE], 4), "médiane_segment": round(med, 4) if pd.notna(med) else None,
                    "rang": f"meilleure que {rk[0]} sur {rk[1]}" if rk else "n/a",
                    "alerte": "; ".join(notes)})
    return pd.DataFrame(out)

CLASSEMENT = classer(DF)
CLASSEMENT.sort_values("valeur", ascending=False).head(10)

#@title Meilleurs jours, heures, formats, canaux
def top(d, col, m=None):
    m = m or METRIQUE_PRINCIPALE
    if col not in d or d[col].notna().sum() == 0: return None
    t = d.groupby(col)[m].agg(["median","count"]).round(4).sort_values("median", ascending=False)
    t["confiance"] = np.where(t["count"] < SEUIL_ECHANTILLON, "fragile", "correcte")
    return t

COMPORTEMENT = {c: top(DF, c) for c in ["canal","format","jour","heure","type_offre","saison"] if c in DF}
COMPORTEMENT = {k: v for k, v in COMPORTEMENT.items() if v is not None}
COMPORTEMENT["canal"]

#@title Modèle de prédiction (simple, explicable)
CIBLE = {"notoriété":"portee","engagement":"interactions","trafic":"clics","conversion":"conversions","fidélisation":"interactions"}[OBJECTIF]
if CIBLE not in DF or DF[CIBLE].notna().sum() == 0:
    CIBLE = "clics" if "clics" in DF and DF["clics"].notna().any() else ("impressions" if "impressions" in DF else None)
CATS = [c for c in ["canal","format","jour","saison","type_offre"] if c in DF]
NUMS = [c for c in ["budget","heure","duree_jours"] if c in DF]

def entrainer(d):
    if CIBLE is None: return None, None, None, "Aucune cible à prédire dans vos données."
    d = d[d[CIBLE].notna()].copy()
    if len(d) < 30:
        return None, None, None, f"Seulement {len(d)} lignes exploitables : prédiction non fiable (minimum conseillé 30)."
    X, y = d[CATS + NUMS].copy(), d[CIBLE].astype(float)
    X[NUMS] = X[NUMS].fillna(X[NUMS].median())
    pre = ColumnTransformer([("c", OneHotEncoder(handle_unknown="ignore"), CATS)], remainder="passthrough")
    mod = Pipeline([("pre", pre), ("m", GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=0))])
    pred = cross_val_predict(mod, X, y, cv=KFold(5, shuffle=True, random_state=0))
    mask = y > 0
    if mask.sum() < 10: return None, None, None, "Trop peu de valeurs non nulles pour évaluer la prédiction."
    mape = float(np.mean(np.abs((y[mask] - pred[mask]) / y[mask])) * 100)
    ratios = y[mask] / np.maximum(pred[mask], 1e-9)
    bornes = (float(np.quantile(ratios, 0.1)), float(np.quantile(ratios, 0.9)))
    mod.fit(X, y)
    return mod, mape, bornes, None

MODELE, MAPE, BORNES, ERR = entrainer(DF)
if ERR: print("ℹ️", ERR)
else:
    ok = "atteint ✅" if MAPE < OBJECTIF_MAPE else "NON atteint ⚠️"
    print(f"Cible prédite : {CIBLE} | erreur moyenne (MAPE, validation croisée) : {MAPE:.1f} % | objectif < {OBJECTIF_MAPE} % : {ok}")
    if MAPE >= OBJECTIF_MAPE:
        print("-> Les prévisions sont des ordres de grandeur. Plus de campagnes passées amélioreront le modèle.")

#@title Simulateur « et si ? » (nouvelle campagne) { run: "auto" }

PREVISION = None
SIM_ON = globals().get("SIM_ON", True)
if MODELE is not None and SIM_ON:
    ligne = {"canal":CANAL_NEW.lower(),"format":FORMAT_NEW.lower(),"jour":JOUR_NEW,"saison":SAISON_NEW,"type_offre":OFFRE_NEW,
             "budget":BUDGET_NEW,"heure":HEURE_NEW,"duree_jours":DUREE_NEW}
    x = pd.DataFrame([{c: ligne.get(c) for c in CATS + NUMS}])
    p = float(MODELE.predict(x)[0])
    PREVISION = {"cible": CIBLE, "valeur": p, "bas": p * BORNES[0], "haut": p * BORNES[1]}
    print(f"Prévision « {CIBLE} » : {p:,.0f} (fourchette 80 % : {PREVISION['bas']:,.0f} à {PREVISION['haut']:,.0f})".replace(",", " "))
    if CANAL_NEW.lower() not in set(DF["canal"]): print(f"Note : le canal « {CANAL_NEW} » n'existe pas dans vos données, la prévision est moins fiable.")
    print(f"Fiabilité : erreur moyenne historique {MAPE:.0f} %. Estimation, pas promesse.")
elif MODELE is None:
    print("Pas de prévision :", ERR)

if DEMO_MODE and (A_IMPRESSIONS == 0 or B_IMPRESSIONS == 0):
    A_IMPRESSIONS, A_CLICS, B_IMPRESSIONS, B_CLICS = 5000, 40, 5000, 62
#@title Comparer deux variantes A et B { run: "auto" }

AB = None
if min(A_IMPRESSIONS, B_IMPRESSIONS) > 0:
    pa, pb = A_CLICS / A_IMPRESSIONS, B_CLICS / B_IMPRESSIONS
    p = (A_CLICS + B_CLICS) / (A_IMPRESSIONS + B_IMPRESSIONS)
    se = np.sqrt(p * (1 - p) * (1 / A_IMPRESSIONS + 1 / B_IMPRESSIONS))
    z = (pb - pa) / se if se > 0 else 0
    pv = 2 * (1 - stats.norm.cdf(abs(z)))
    AB = {"pa": pa, "pb": pb, "pv": pv}
    print(f"CTR A = {pa:.2%} | CTR B = {pb:.2%} | p-value = {pv:.3f}")
    if pv < 0.05:
        print("Différence significative :", "B" if pb > pa else "A", "est meilleure. À valider par un humain avant de basculer le budget.")
    else:
        print("Différence NON significative : ne pas conclure, poursuivre le test ou augmenter l'échantillon.")
else:
    print("Pas de test A/B : saisissez les impressions et clics de vos deux variantes ci-dessus, puis relancez la cellule.")


POS = set("super bravo merci génial magnifique excellent top parfait adore aime bien belle beau incroyable félicitations réussi bonheur love cool formidable".split())
NEG = set("nul nulle mauvais mauvaise décevant déçu déception honte arnaque problème bug cassé horrible dommage coupé catastrophe scandale lamentable triste colère".split())
NEGATIONS = {"pas","jamais","aucun","ne","n'"}

def sentiment(txt):
    mots = [m.strip(".,!?;:()\"'") for m in str(txt).lower().split()]
    sc = 0
    for i, m in enumerate(mots):
        v = 1 if m in POS else -1 if m in NEG else 0
        if v and any(x in mots[max(0, i-2):i] for x in NEGATIONS): v = -v
        sc += v
    return "positif" if sc > 0 else "négatif" if sc < 0 else "neutre"

COMM = None
if DEMO_MODE:
    rng = np.random.default_rng(3)
    phrases = ["Super diffusion, magnifique finale, merci pour le direct","Dommage, le son était coupé au début","Ça commence à quelle heure ?",
               "Bravo à toute l'équipe, excellent","Franchement nul, déçu par la qualité","Merci pour le partage","Ah bravo la technique, du grand art !",
               "Ce n'est pas bien du tout","Vraiment top, j'adore"]
    n = 120
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq="6h")
    txt = rng.choice(phrases, n, p=[.14,.12,.12,.12,.1,.12,.06,.07,.15])
    for i in range(80, n):
        if rng.random() < .45: txt[i] = rng.choice(["Honte, problème encore", "Arnaque, nul", "Dommage, catastrophe"])
    COMM = pd.DataFrame({"date": dates, "commentaire": txt})
elif COMM_BRUT is not None:
    COMM = COMM_BRUT.copy()
    COMM.columns = [c.lower() for c in COMM.columns]
    if "commentaire" not in COMM:
        col = [c for c in COMM.columns if c in ("text","texte","comment","message","commentaires")]
        if col: COMM = COMM.rename(columns={col[0]: "commentaire"})
        else:
            print("Colonne de texte introuvable (attendu : commentaire, text, message)."); COMM = None

SENT, ALERTE_TXT = None, "Aucun commentaire analysé."
if COMM is not None and "commentaire" in COMM:
    COMM["sentiment"] = COMM["commentaire"].map(sentiment)
    SENT = COMM["sentiment"].value_counts(normalize=True).mul(100).round(1)
    print(SENT.to_string())
    if len(COMM) < 30: print("ATTENTION : moins de 30 commentaires, résultat sans valeur statistique.")
    if SENT.get("neutre", 0) > 50: print("Note : plus de 50 % de neutres, souvent des questions factuelles qui n'indiquent pas la satisfaction.")
    if "date" in COMM:
        COMM["date"] = pd.to_datetime(COMM["date"], errors="coerce")
        fin = COMM["date"].max()
        recent = COMM[COMM["date"] > fin - pd.Timedelta(days=7)]
        avant = COMM[(COMM["date"] <= fin - pd.Timedelta(days=7)) & (COMM["date"] > fin - pd.Timedelta(days=14))]
        nr = (recent["sentiment"] == "négatif").mean() * 100 if len(recent) else 0
        na_ = (avant["sentiment"] == "négatif").mean() * 100 if len(avant) else 0
        ALERTE_TXT = f"Négatifs sur 7 jours : {nr:.0f} % (semaine précédente : {na_:.0f} %)."
        if nr >= SEUIL_ALERTE_NEG and nr > na_:
            ALERTE_TXT += " ALERTE : hausse des commentaires négatifs. Procédure conseillée : 1) vérifier les faits, 2) évaluer la gravité, 3) identifier les publics concernés, 4) préparer une réponse. L'humain décide de la prise de parole."
        print(ALERTE_TXT)
    print("Verbatims négatifs (exemples) :", COMM[COMM["sentiment"] == "négatif"]["commentaire"].head(3).tolist())
else:
    print("Pas de commentaires analysés (étape facultative).")


#@title Tableau de bord final (HTML téléchargeable)
PAL = ["#E6007E","#7C3AED","#F59E0B","#10B981","#3B82F6","#EF4444","#14B8A6","#8B5CF6"]
ROSE, VIOLET, GRIS = "#E6007E", "#7C3AED", "#6B6780"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "axes.edgecolor": "#D9D6E5", "axes.labelcolor": GRIS, "xtick.color": GRIS, "ytick.color": GRIS})

def fig_b64(fig):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=120, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return base64.b64encode(b.getvalue()).decode()

def habiller(ax, titre):
    ax.set_title(titre, loc="left", fontsize=12, fontweight="bold", color="#1F1B2E", pad=10)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#EEEAF6", lw=.8); ax.set_axisbelow(True)

def fmt_pct(x): return f"{x*100:.1f} %"
NOM_M = {"taux_conversion":"Taux de conversion","ctr":"CTR","taux_engagement":"Taux d'engagement","portee":"Portée","impressions":"Impressions","vues":"Vues"}.get(METRIQUE_PRINCIPALE, METRIQUE_PRINCIPALE)
EST_TAUX = METRIQUE_PRINCIPALE in ("taux_conversion","ctr","taux_engagement")
def fm(x): return fmt_pct(x) if EST_TAUX else f"{x:,.0f}".replace(",", " ")

GRAPHES = []   # (largeur 1 ou 2, titre, image)

# 1) indicateur principal par canal
t = COMPORTEMENT.get("canal")
if t is not None:
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    vals = t["median"]; bars = ax.bar(vals.index.astype(str), vals.values, color=[PAL[i % len(PAL)] for i in range(len(vals))], width=.62)
    for b, v in zip(bars, vals.values): ax.text(b.get_x()+b.get_width()/2, v, fm(v), ha="center", va="bottom", fontsize=8.5, color="#1F1B2E")
    habiller(ax, f"{NOM_M} médian par canal"); plt.xticks(rotation=25, ha="right")
    GRAPHES.append((1, "canal", fig_b64(fig)))

# 2) tendance
if "date" in DF and DF["date"].notna().sum() > 5:
    s = DF.dropna(subset=["date", METRIQUE_PRINCIPALE]).sort_values("date").set_index("date")[METRIQUE_PRINCIPALE]
    if len(s) > 5:
        r = s.rolling(7, min_periods=3).median()
        fig, ax = plt.subplots(figsize=(5.4, 3.4))
        ax.fill_between(r.index, r.values, color=VIOLET, alpha=.15); ax.plot(r.index, r.values, color=VIOLET, lw=2.2)
        ax.scatter(s.index, s.values, s=10, color=ROSE, alpha=.35)
        habiller(ax, f"{NOM_M} dans le temps (médiane glissante)"); fig.autofmt_xdate()
        GRAPHES.append((1, "tendance", fig_b64(fig)))

# 3) benchmark
if len(BENCH):
    b = BENCH.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    labels = [f"{c} · {f}" if f != "tous formats" else c for c, f in zip(b["canal"], b["format"])]
    ax.barh(labels, b["médiane"], color=[ROSE if c == "correcte" else "#F7A8D0" for c in b["confiance"]], height=.62)
    for i, (v, n) in enumerate(zip(b["médiane"], b["n"])): ax.text(v, i, f"  n={n}", va="center", fontsize=8, color=GRIS)
    habiller(ax, "Benchmark par segment (rose clair = échantillon fragile)"); ax.grid(axis="x", color="#EEEAF6"); ax.grid(axis="y", visible=False)
    GRAPHES.append((1, "benchmark", fig_b64(fig)))

# 4) heatmap jour x heure
if "jour" in DF and "heure" in DF:
    hm = DF.pivot_table(index="jour", columns="heure", values=METRIQUE_PRINCIPALE, aggfunc="median")
    hm = hm.reindex([j for j in ORDRE_JOURS if j in hm.index])
    if hm.shape[0] >= 2 and hm.shape[1] >= 2:
        fig, ax = plt.subplots(figsize=(5.4, 3.4))
        im = ax.imshow(hm.values, cmap="RdPu", aspect="auto")
        ax.set_xticks(range(hm.shape[1])); ax.set_xticklabels([f"{int(h)}h" for h in hm.columns]); ax.set_yticks(range(hm.shape[0])); ax.set_yticklabels(hm.index)
        ax.set_title("Meilleurs créneaux : jour × heure", loc="left", fontsize=12, fontweight="bold", color="#1F1B2E", pad=10)
        for s_ in ax.spines.values(): s_.set_visible(False)
        plt.colorbar(im, ax=ax, fraction=.03, pad=.02)
        GRAPHES.append((1, "creneaux", fig_b64(fig)))

# 5) coût vs performance par canal
if "cpa" in DF and DF["cpa"].notna().any() and METRIQUE_PRINCIPALE in DF:
    g = DF.groupby("canal").agg(cpa=("cpa", "median"), perf=(METRIQUE_PRINCIPALE, "median"), n=("canal", "size")).dropna()
    if len(g) >= 2:
        fig, ax = plt.subplots(figsize=(5.4, 3.4))
        for i, (c, r) in enumerate(g.iterrows()):
            ax.scatter(r["cpa"], r["perf"], s=60 + r["n"] * 8, color=PAL[i % len(PAL)], alpha=.85, edgecolor="white")
            ax.annotate(c, (r["cpa"], r["perf"]), textcoords="offset points", xytext=(8, 6), fontsize=8.5)
        ax.set_xlabel("Coût par action (plus bas = mieux)"); ax.set_ylabel(NOM_M)
        habiller(ax, "Coût et performance par canal (haut-gauche = idéal)"); ax.grid(axis="x", color="#EEEAF6")
        GRAPHES.append((1, "cout", fig_b64(fig)))

# 6) sentiment
if SENT is not None:
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    ordre = [k for k in ["positif", "neutre", "négatif"] if k in SENT.index]
    ax.pie([SENT[k] for k in ordre], labels=[f"{k} {SENT[k]:.0f} %" for k in ordre], colors=[{"positif":"#10B981","neutre":"#C9C5DA","négatif":ROSE}[k] for k in ordre],
           startangle=90, wedgeprops=dict(width=.38, edgecolor="white"), textprops=dict(fontsize=9, color="#1F1B2E"))
    ax.set_title("Sentiment des commentaires", loc="left", fontsize=12, fontweight="bold", color="#1F1B2E")
    GRAPHES.append((1, "sentiment", fig_b64(fig)))

# 7) A/B
if AB is not None:
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    bars = ax.bar(["Variante A", "Variante B"], [AB["pa"], AB["pb"]], color=[VIOLET, ROSE], width=.5)
    for bb, v in zip(bars, [AB["pa"], AB["pb"]]): ax.text(bb.get_x()+bb.get_width()/2, v, f"{v:.2%}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    habiller(ax, "Test A/B : CTR" + (" (différence significative)" if AB["pv"] < .05 else " (différence NON significative)"))
    GRAPHES.append((1, "ab", fig_b64(fig)))

# 8) prévision
if PREVISION is not None:
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    ax.hlines(0, PREVISION["bas"], PREVISION["haut"], color="#F7A8D0", lw=18, capstyle="round")
    ax.scatter([PREVISION["valeur"]], [0], s=260, color=ROSE, zorder=3, edgecolor="white", linewidth=2)
    ax.text(PREVISION["valeur"], .22, f"{PREVISION['valeur']:,.0f}".replace(",", " "), ha="center", fontsize=12, fontweight="bold", color=ROSE)
    ax.text(PREVISION["bas"], -.28, f"{PREVISION['bas']:,.0f}".replace(",", " "), ha="center", fontsize=8.5, color=GRIS)
    ax.text(PREVISION["haut"], -.28, f"{PREVISION['haut']:,.0f}".replace(",", " "), ha="center", fontsize=8.5, color=GRIS)
    ax.set_ylim(-.6, .6); ax.set_yticks([])
    for s_ in ["top", "right", "left"]: ax.spines[s_].set_visible(False)
    ax.set_title(f"Prévision « {PREVISION['cible']} » (fourchette 80 %)", loc="left", fontsize=12, fontweight="bold", color="#1F1B2E")
    GRAPHES.append((1, "prevision", fig_b64(fig)))

# ---- cartes chiffres clés
def med(c): return DF[c].median() if c in DF and DF[c].notna().any() else None
CARTES = [("Publications", f"{len(DF)}", f"{DF['canal'].nunique()} canaux")]
for c, nom, f in [("ctr","CTR",fmt_pct), ("taux_conversion","Conversion",fmt_pct), ("taux_engagement","Engagement",fmt_pct),
                  ("cpa","Coût / action",lambda v: f"{v:.2f} €"), ("roas","ROAS",lambda v: f"{v:.2f}")]:
    v = med(c)
    if v is not None and not np.isnan(v): CARTES.append((nom, f(v), "médiane"))
if MAPE is not None: CARTES.append(("Erreur de prévision", f"{MAPE:.0f} %", f"objectif < {OBJECTIF_MAPE} %"))

def recommandations():
    rec, meilleur_canal = [], None
    for c in ["canal","format","jour","heure"]:
        t = COMPORTEMENT.get(c)
        if t is not None and len(t) > 1:
            m, fiable = t.index[0], t.iloc[0]["confiance"]
            if c == "canal": meilleur_canal = m
            suffixe = "" if fiable == "correcte" else " : échantillon faible, à confirmer avant toute décision"
            rec.append(f"Piste : <b>{c} = {m}</b> (médiane {NOM_M.lower()} : {fm(t.iloc[0]['median'])}, confiance {fiable}){suffixe}.")
    if "cpa" in DF and DF["cpa"].notna().any():
        cp = DF.groupby("canal")["cpa"].median().dropna().sort_values()
        if len(cp) > 1:
            rec.append(f"Coût par action le plus bas : <b>{cp.index[0]}</b> ({cp.iloc[0]:.2f} €) ; le plus élevé : {cp.index[-1]} ({cp.iloc[-1]:.2f} €).")
            if meilleur_canal is not None and meilleur_canal != cp.index[0] and meilleur_canal in cp.index:
                rec.append(f"<b>À arbitrer</b> : {meilleur_canal} a le meilleur {NOM_M.lower()} mais {cp.index[0]} coûte moins cher par action (CPA {cp.iloc[0]:.2f} € contre {cp[meilleur_canal]:.2f} €). Choisir selon l'objectif (volume ou coût) avant de déplacer du budget.")
    if AB is not None:
        rec.append("Test A/B : " + (f"la variante {'B' if AB['pb'] > AB['pa'] else 'A'} est meilleure (p = {AB['pv']:.3f})." if AB["pv"] < .05 else f"différence non significative (p = {AB['pv']:.3f}) : ne pas conclure."))
    if PREVISION: rec.append(f"Prévision pour la campagne simulée : {PREVISION['valeur']:,.0f} {PREVISION['cible']} (fourchette {PREVISION['bas']:,.0f} à {PREVISION['haut']:,.0f}).".replace(",", " "))
    rec.append(f"Profil <b>{PROFIL}</b> : ton {P['ton']}. {P['regle']}")
    return rec

def limites():
    l = ["Les chiffres montrent ce qui s'est passé, pas pourquoi : la causalité n'est pas démontrée.",
         "Les statistiques dépendent de la visibilité donnée par les algorithmes et ne voient pas le hors-ligne.",
         "Exports agrégés : analyse par segments, pas par individu."]
    if MAPE is not None and MAPE >= OBJECTIF_MAPE: l.append(f"Précision du modèle ({MAPE:.0f} %) au-dessus de l'objectif de {OBJECTIF_MAPE} % : prévisions indicatives.")
    if SENT is not None: l.append("Sentiment : ironie, jargon local et second degré mal détectés ; les commentateurs ne représentent pas la majorité silencieuse.")
    l += [f"Import : {r}" for r in RAPPORT_IMPORT]
    return l

ALERTE_BLOC = ""
if SENT is not None and "ALERTE" in ALERTE_TXT:
    ALERTE_BLOC = f'<div class="alerte">🚨 {ALERTE_TXT}</div>'

cartes_html = "".join(f'<div class="carte"><div class="cv">{v}</div><div class="cn">{n}</div><div class="cs">{s}</div></div>' for n, v, s in CARTES)
graph_html = "".join(f'<div class="graphe"><img src="data:image/png;base64,{img}"></div>' for _, _, img in GRAPHES)
recs_html = "".join(f"<li>{r}</li>" for r in recommandations())
lims_html = "".join(f"<li>{l}</li>" for l in limites())
bandeau = '<div class="demo">Données fictives (démo)</div>' if DEMO_MODE else ""

HTML_DASH = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tableau de bord de campagne</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:#F6F3FB;color:#1F1B2E}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 16px 40px}}
.hero{{background:linear-gradient(120deg,#E6007E,#7C3AED);color:#fff;padding:28px 24px;border-radius:0 0 22px 22px}}
.hero h1{{margin:0 0 6px;font-size:26px}} .hero p{{margin:0;opacity:.92;font-size:14px}}
.demo{{display:inline-block;background:#FFF3C4;color:#7A5B00;padding:3px 10px;border-radius:99px;font-size:12px;font-weight:bold;margin-bottom:8px}}
.cartes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:-18px 0 18px}}
.carte{{background:#fff;border-radius:16px;padding:14px 16px;box-shadow:0 4px 14px rgba(124,58,237,.10)}}
.cv{{font-size:26px;font-weight:bold;color:#E6007E}} .cn{{font-size:13px;font-weight:bold;margin-top:2px}} .cs{{font-size:11px;color:#6B6780}}
.grille{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
.graphe{{background:#fff;border-radius:16px;padding:10px;box-shadow:0 4px 14px rgba(124,58,237,.08)}} .graphe img{{width:100%;height:auto;display:block}}
.bloc{{background:#fff;border-radius:16px;padding:16px 20px;margin-top:14px;box-shadow:0 4px 14px rgba(124,58,237,.08)}}
.bloc h2{{margin:0 0 8px;font-size:16px;color:#7C3AED}} .bloc li{{margin:6px 0;font-size:14px;line-height:1.45}}
.alerte{{background:#FDE8F3;border-left:6px solid #E6007E;padding:12px 16px;border-radius:12px;margin:14px 0;font-size:14px}}
.note{{font-size:12px;color:#6B6780;margin-top:14px}}
</style></head><body>
<div class="hero"><div class="wrap" style="padding-bottom:0">{bandeau}<h1>Tableau de bord de campagne</h1>
<p>{dt.date.today():%d/%m/%Y} · profil {PROFIL} · objectif {OBJECTIF} · {len(DF)} publications analysées</p></div></div>
<div class="wrap">
<div class="cartes">{cartes_html}</div>
{ALERTE_BLOC}
<div class="grille">{graph_html}</div>
<div class="bloc"><h2>Recommandations <small style="color:#6B6780;font-weight:normal">(l'IA recommande, l'humain décide)</small></h2><ul>{recs_html}</ul></div>
<div class="bloc"><h2>Limites et niveau de confiance</h2><ul>{lims_html}</ul></div>
<p class="note">{FORMULE}. Benchmark : médiane de l'historique propre, par canal et format, à {AGE_COMPARAISON_H} h (± {TOLERANCE_AGE_H} h). Moins de {SEUIL_ECHANTILLON} publications = « fragile ».</p>
</div></body></html>"""

# Le HTML est dans la variable HTML_DASH (l'appli le propose en téléchargement).