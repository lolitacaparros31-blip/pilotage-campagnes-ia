"""Rapport PDF de Lumen (reportlab, sans dépendance système).

construire_pdf(d) reçoit des données simples (textes, tableaux, images PNG) et renvoie les octets du PDF :
la mise en page est ici, le calcul reste dans l'application.
"""
import io
import os
import re
import base64

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import math
import textwrap
from matplotlib.backends.backend_pdf import PdfPages

try:
    import reportlab  # noqa: F401
    AVEC_REPORTLAB = True
except Exception:          # module absent : on bascule sur le PDF de secours (matplotlib seul), sans casser l'appli
    AVEC_REPORTLAB = False


def _texte(t):
    import re as _re
    t = _re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]", "", str(t)).replace("<br/>", " ").replace("<br>", " ")
    return _re.sub(r"<[^>]+>", "", t).replace("&nbsp;", " ").replace("&amp;", "&").strip()


def pdf_secours(d):
    """PDF simple (matplotlib uniquement) : mêmes informations, mise en page plus sobre, cadre bordeaux conservé."""
    BORD, POS, FUC, GRIS = "#722035", "#123955", "#9E2C6A", "#5B6470"
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        def page():
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.patches.append(matplotlib.patches.Rectangle((0.006, 0.004), 0.988, 0.992, fill=False, ec=BORD, lw=7, transform=fig.transFigure))
            fig.text(0.07, 0.955, "Lumen", fontsize=14, fontweight="bold", color=POS, family="serif")
            fig.text(0.93, 0.955, d.get("entete", ""), fontsize=8, color=GRIS, ha="right")
            fig.text(0.07, 0.03, "Plateforme d'analyse de campagnes générée par IA · Mia propose, vous décidez.", fontsize=7, color=GRIS)
            return fig
        fig = page(); y = 0.9
        def ecrire(txt, taille=9.5, couleur=POS, gras=False, largeur=95, esp=0.021, fam=None):
            nonlocal y
            for ligne in textwrap.wrap(_texte(txt), largeur) or [""]:
                fig.text(0.07, y, ligne, fontsize=taille, color=couleur, fontweight="bold" if gras else "normal", family=fam or "sans-serif"); y -= esp
        ecrire(d.get("titre", "Rapport de campagne"), 22, POS, True, 60, 0.04, "serif")
        ecrire(d.get("sous_titre", ""), 8.5, GRIS, False, 120, 0.018)
        if d.get("demo"): ecrire(d["demo"], 8, "#4A4320", True)
        y -= 0.012
        if d.get("bilan"): ecrire("Mia · le bilan", 11, FUC, True); ecrire(d["bilan"], 9.5, POS, False, 100)
        for _, t in d.get("alertes", []): y -= 0.006; ecrire("• " + t, 9, POS, False, 104)
        y -= 0.012; ecrire("Chiffres clés", 13, BORD, True, 60, 0.03, "serif")
        ecrire("   ·   ".join(f"{n} : {v}" for n, v, _ in d.get("kpis", [])), 9.5, POS, False, 100)
        y -= 0.012; ecrire("Vos campagnes", 13, BORD, True, 60, 0.03, "serif")
        for c in d.get("campagnes", []):
            ecrire(f"{c['nom']}  —  {c['statut']}  ·  {c['kpi']} : {c['valeur']}  ·  {c['evolution']}  ·  {c['publications']} publ.", 8.8, POS, False, 112, 0.019)
        y -= 0.012; ecrire("Vos priorités", 13, BORD, True, 60, 0.03, "serif")
        for i, (t, _, x) in enumerate(d.get("priorites", []), 1): ecrire(f"{i}. {t} : {x}", 9, POS, False, 108)
        pdf.savefig(fig); plt.close(fig)
        fig = page(); y = 0.9
        graphes = [g[1] for g in d.get("graphes", [])][:4]
        graphes = [g for g in graphes if g]
        ecrire("Les graphiques", 13, BORD, True, 60, 0.03, "serif")
        for k, png in enumerate(graphes[:4]):
            im = matplotlib.image.imread(io.BytesIO(png), format="png")
            ax = fig.add_axes([0.07 + (k % 2) * 0.45, 0.58 - (k // 2) * 0.3, 0.42, 0.26]); ax.imshow(im); ax.axis("off")
        y = 0.27
        ecrire("Les recommandations de Mia", 13, BORD, True, 60, 0.03, "serif")
        for r in d.get("recommandations", [])[:4]: ecrire("• " + r, 8.8, POS, False, 112, 0.019)
        pdf.savefig(fig); plt.close(fig)
    return buf.getvalue()

if AVEC_REPORTLAB:
    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle)

    POSEIDON, FUCHSIA, BORDEAUX = colors.HexColor("#123955"), colors.HexColor("#9E2C6A"), colors.HexColor("#722035")
    NEPTUNE, SPICE, ALL_ABOARD, ACACIA = colors.HexColor("#5FA787"), colors.HexColor("#884332"), colors.HexColor("#5D9BCB"), colors.HexColor("#B7A93A")
    GRIS, ROSE_PALE = colors.HexColor("#5B6470"), colors.HexColor("#FBF3F7")

    _FONTS = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    for nom, fichier in (("Lumen", "DejaVuSans.ttf"), ("Lumen-Bold", "DejaVuSans-Bold.ttf"), ("Lumen-Italic", "DejaVuSans-Oblique.ttf"),
                         ("Lumen-Serif", "DejaVuSerif.ttf"), ("Lumen-Serif-Bold", "DejaVuSerif-Bold.ttf")):
        pdfmetrics.registerFont(TTFont(nom, os.path.join(_FONTS, fichier)))
    pdfmetrics.registerFontFamily("Lumen", normal="Lumen", bold="Lumen-Bold", italic="Lumen-Italic", boldItalic="Lumen-Bold")

    _EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿️]")


    def propre(texte):
        """Texte sûr pour reportlab : emojis retirés, entités HTML normalisées, balises <b> et <br> conservées."""
        t = _EMOJI.sub("", str(texte)).replace("&nbsp;", " ").replace("<br>", "<br/>")
        t = re.sub(r"&(?!amp;|lt;|gt;)", "&amp;", t)
        t = re.sub(r"<(?!/?b>|br/>|/?i>)", "&lt;", t)
        return t.strip()


    COUL = {"fort": "#5FA787", "moyen": "#5D9BCB", "faible": "#884332"}


    def _png(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=170, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return buf.getvalue()


    def graphe_ecarts(camps, titre):
        """Barres : évolution (ou écart à la médiane) de chaque campagne, comparable même si les indicateurs diffèrent."""
        pts = [(c["nom"], c["ecart"], COUL.get(c["style"], "#999")) for c in camps if c.get("ecart") is not None and not (isinstance(c["ecart"], float) and math.isnan(c["ecart"]))]
        if not pts:
            return None
        pts.sort(key=lambda x: x[1])
        fig, ax = plt.subplots(figsize=(6.2, 0.5 * len(pts) + 1.3))
        barres = ax.barh([x[0] for x in pts], [x[1] for x in pts], color=[x[2] for x in pts], height=.62)
        for b, x in zip(barres, pts):
            ax.text(x[1], b.get_y() + b.get_height() / 2, f"  {x[1]:+.0f} %", va="center", ha="left" if x[1] >= 0 else "right", fontsize=8, color="#123955")
        ax.axvline(0, color="#5B6470", lw=.8)
        ax.set_title(titre, loc="left", fontsize=10.5, fontweight="bold", color="#123955")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=8, colors="#5B6470")
        ax.margins(x=.18)
        return _png(fig)


    def graphe_courbes(series, titre):
        """Une petite courbe par campagne, chacune à sa propre échelle (indicateurs différents)."""
        series = [x for x in series if x.get("valeurs") and len(x["valeurs"]) >= 3]
        if not series:
            return None
        n, cols = len(series), 2
        lignes = math.ceil(n / cols)
        fig, axes = plt.subplots(lignes, cols, figsize=(6.2, 1.35 * lignes + .5), squeeze=False)
        for ax in axes.flat:
            ax.axis("off")
        for ax, x in zip(axes.flat, series):
            ax.axis("on")
            couleur = COUL.get(x["style"], "#123955")
            ax.plot(x["dates"], x["valeurs"], color=couleur, lw=1.8)
            ax.fill_between(x["dates"], x["valeurs"], min(x["valeurs"]), color=couleur, alpha=.12)
            ax.set_title(f"{x['nom']}  ·  {x['kpi']}", loc="left", fontsize=7.5, color="#123955", fontweight="bold")
            ax.set_yticks([])
            ax.tick_params(labelsize=6.5, colors="#5B6470")
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
            for sp in ("top", "right", "left"):
                ax.spines[sp].set_visible(False)
        fig.suptitle(titre, x=0.01, ha="left", fontsize=10.5, fontweight="bold", color="#123955", y=1.0)
        fig.tight_layout()
        return _png(fig)


    def _style(nom, **kw):
        base = dict(fontName="Lumen", fontSize=9.5, leading=13.5, textColor=POSEIDON, alignment=TA_LEFT)
        base.update(kw)
        return ParagraphStyle(nom, **base)


    S = {
        "titre": _style("titre", fontName="Lumen-Serif-Bold", fontSize=24, leading=28),
        "sous": _style("sous", fontSize=9.5, textColor=GRIS, leading=13),
        "h2": _style("h2", fontName="Lumen-Serif-Bold", fontSize=14, leading=18, spaceBefore=12, spaceAfter=5, textColor=BORDEAUX),
        "txt": _style("txt"), "petit": _style("petit", fontSize=8.5, leading=11.5, textColor=GRIS),
        "kv": _style("kv", fontName="Lumen-Serif", fontSize=17, leading=20), "kl": _style("kl", fontSize=8, leading=10, textColor=GRIS),
        "entete": _style("entete", fontName="Lumen-Bold", fontSize=8.5, textColor=colors.white), "cel": _style("cel", fontSize=8.5, leading=11),
        "puce": _style("puce", leftIndent=10, bulletIndent=0, spaceAfter=3),
    }


    def _encadre(contenu, couleur_barre, fond=ROSE_PALE, largeur=None):
        t = Table([[contenu]], colWidths=[largeur] if largeur else None)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fond), ("LINEBEFORE", (0, 0), (0, -1), 3.2, couleur_barre),
                               ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                               ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        return t


    def _image(png, largeur):
        w, h = PILImage.open(io.BytesIO(png)).size
        return Image(io.BytesIO(png), width=largeur, height=largeur * h / w)


    def _decor(canvas, doc, entete):
        largeur, hauteur = A4
        canvas.saveState()
        canvas.setStrokeColor(BORDEAUX)
        canvas.setLineWidth(9)
        canvas.rect(4.5, 4.5, largeur - 9, hauteur - 9)
        canvas.setFont("Lumen-Serif-Bold", 12)
        canvas.setFillColor(POSEIDON)
        canvas.drawString(1.8 * cm, hauteur - 1.35 * cm, "Lumen")
        canvas.setFont("Lumen", 7.5)
        canvas.setFillColor(GRIS)
        canvas.drawRightString(largeur - 1.8 * cm, hauteur - 1.35 * cm, entete)
        canvas.drawString(1.8 * cm, 1.15 * cm, "Plateforme d'analyse de campagnes générée par IA · Mia propose, vous décidez.")
        canvas.drawRightString(largeur - 1.8 * cm, 1.15 * cm, f"Page {doc.page}")
        canvas.restoreState()


    def construire_pdf(d):
        """d : titre, sous_titre, entete, demo (str ou ''), bilan, alertes [(style, txt)], kpis [(nom, valeur, sous)],
        campagnes [dict nom/statut/style/kpi/valeur/evolution/publications], graphes [(titre, png)],
        priorites [(titre, style, txt)], recommandations [txt], limites [txt]."""
        buf = io.BytesIO()
        doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=2.1 * cm, bottomMargin=1.7 * cm,
                              title=d.get("titre", "Rapport Lumen"), author="Lumen")
        doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                                           onPage=lambda c, dd: _decor(c, dd, d.get("entete", "")))])
        L = doc.width
        story = [Paragraph(propre(d.get("titre", "Rapport de campagne")), S["titre"]), Spacer(1, 3), Paragraph(propre(d.get("sous_titre", "")), S["sous"])]
        if d.get("demo"):
            badge = Table([[Paragraph(f"<b>{propre(d['demo'])}</b>", _style("b", fontSize=8, textColor=colors.HexColor("#4A4320")))]], colWidths=[None])
            badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFE6A8")), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
            badge.hAlign = "LEFT"
            story += [Spacer(1, 6), badge]
        story.append(Spacer(1, 10))

        if d.get("bilan"):
            story += [_encadre([Paragraph("<b>Mia · le bilan</b>", _style("mb", textColor=FUCHSIA, fontSize=10)), Spacer(1, 3), Paragraph(propre(d["bilan"]), S["txt"])], FUCHSIA, largeur=L), Spacer(1, 8)]
        for style, txt in d.get("alertes", []):
            story += [_encadre(Paragraph(propre(txt), S["txt"]), {"faible": SPICE, "fort": NEPTUNE}.get(style, ACACIA), fond=colors.HexColor("#F8F4F5"), largeur=L), Spacer(1, 5)]

        # chiffres clés : 4 par ligne
        kpis = d.get("kpis", [])
        if kpis:
            story.append(Paragraph("Chiffres clés", S["h2"]))
            lignes = [kpis[i:i + 4] for i in range(0, len(kpis), 4)]
            for lg in lignes:
                cells = [[Paragraph(propre(v), S["kv"]), Paragraph(propre(n), S["kl"])] for n, v, _ in lg] + [[""]] * (4 - len(lg))
                t = Table([[c[0] if c else "" for c in cells], [c[1] if len(c) > 1 else "" for c in cells]], colWidths=[L / 4] * 4)
                t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.white), ("BOX", (0, 0), (-1, -1), 0, colors.white), ("LINEBELOW", (0, 1), (-1, 1), 0, colors.white),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
                                       ("LINEBEFORE", (0, 0), (-1, -1), 0.6, colors.HexColor("#EADDE0"))]))
                story += [t, Spacer(1, 3)]

        # tableau des campagnes
        camps = d.get("campagnes", [])
        if camps:
            data = [[Paragraph(x, S["entete"]) for x in ("Campagne", "Situation", "Indicateur", "Valeur", "Évolution", "Publ.")]]
            couleurs = {"fort": NEPTUNE, "moyen": ALL_ABOARD, "faible": SPICE}
            for c in camps:
                col = couleurs.get(c.get("style"), GRIS)
                data.append([Paragraph(f"<b>{propre(c['nom'])}</b>", S["cel"]), Paragraph(f'<font color="{col.hexval().replace("0x", "#")}"><b>{propre(c["statut"])}</b></font>', S["cel"]),
                             Paragraph(propre(c["kpi"]), S["cel"]), Paragraph(f"<b>{propre(c['valeur'])}</b>", S["cel"]), Paragraph(propre(c["evolution"]), S["cel"]), Paragraph(str(c["publications"]), S["cel"])])
            t = Table(data, colWidths=[L * 0.30, L * 0.17, L * 0.19, L * 0.12, L * 0.14, L * 0.08], repeatRows=1)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BORDEAUX), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROSE_PALE]),
                                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                                   ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#EADDE0"))]))
            story.append(KeepTogether([Paragraph("Vos campagnes", S["h2"]), t]))

        # priorités
        prio = d.get("priorites", [])
        if prio:
            cases = []
            for i, (titre, style, txt) in enumerate(prio, 1):
                cases.append([Paragraph(f'<font color="#9E2C6A"><b>{i}</b></font>  <b>{propre(titre)}</b>', S["cel"]), Spacer(1, 3), Paragraph(propre(txt), S["cel"])])
            t = Table([cases], colWidths=[L / len(cases)] * len(cases))
            st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F4F5")), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                  ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LINEBEFORE", (1, 0), (-1, -1), 2, colors.white)]
            for k, (_, style, _) in enumerate(prio):
                st.append(("LINEABOVE", (k, 0), (k, 0), 3, {"faible": SPICE, "fort": NEPTUNE}.get(style, ACACIA)))
            t.setStyle(TableStyle(st))
            story.append(KeepTogether([Paragraph("Vos priorités", S["h2"]), t]))

        # graphiques, 2 par ligne
        perso = [("Évolution", graphe_ecarts(camps, "Évolution des campagnes sur 4 semaines" if d.get("hetero") else "Écart de chaque campagne à la médiane")),
                 ("Courbes", graphe_courbes(d.get("series", []), "Évolution hebdomadaire de chaque campagne"))]
        graphes = [(n, g) for n, g in perso if g] + list(d.get("graphes", []))
        graphes = graphes[:6]
        if graphes:
            larg = (L - 0.4 * cm) / 2
            story.append(Paragraph("Les graphiques", S["h2"]))
            for i in range(0, len(graphes), 2):
                ligne = [_image(g[1], larg) for g in graphes[i:i + 2]]
                if len(ligne) == 1:
                    ligne.append("")
                t = Table([ligne], colWidths=[larg + 0.2 * cm] * 2)
                t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
                story.append(KeepTogether(t))

        recs = [r for r in d.get("recommandations", []) if "non précisé" not in str(r)]
        entete = [Paragraph("Les recommandations de Mia", S["h2"]), Paragraph("L'IA recommande, l'humain décide.", S["petit"]), Spacer(1, 3)]
        if recs:
            story.append(KeepTogether(entete + [Paragraph(propre(recs[0]), S["puce"], bulletText="•")]))
            for r in recs[1:]:
                story.append(Paragraph(propre(r), S["puce"], bulletText="•"))
        else:
            story += entete
        if d.get("limites"):
            story.append(Paragraph("Limites de l'analyse", S["h2"]))
            for r in d["limites"]:
                story.append(Paragraph(propre(r), _style("pl", fontSize=8.5, leading=11.5, textColor=GRIS, leftIndent=10, bulletIndent=0, spaceAfter=2), bulletText="•"))
        doc.build(story)
        return buf.getvalue()
else:
    def construire_pdf(d):
        return pdf_secours(d)
