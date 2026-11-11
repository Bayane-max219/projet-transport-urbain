"""Pages d'analyse : tableau de bord, analyse des retards et anomalies, simulation."""
import matplotlib.dates as mdates
from PyQt5.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QSpinBox, QTextBrowser, QVBoxLayout

from view.style import COULEURS
from view.widgets import (Page, bouton, carte, champ_date, champ_jour, formulaire, graphique, habiller, lire_date,
                          lire_periode, remplir, tableau)

NC = "Non calculable"
COLONNES_STATS = [("", "nom"), ("Trajets", "total"), ("Réalisés", "realises"), ("Annulés", "annules"),
                  ("Interrompus", "interrompus"), ("Retard moyen (min)", "retard_moyen"), ("Ponctualité (%)", "ponctualite")]


class PageTableauBord(Page):
    CARTES = ["Lignes actives", "Véhicules disponibles", "Trajets réalisés", "Trajets annulés", "Taux de ponctualité",
              "Retard moyen", "Incidents"]

    def __init__(self):
        super().__init__("Tableau de bord")
        self.du, self.au, self.btn = champ_jour(30), champ_jour(), bouton("Actualiser")
        barre = QHBoxLayout()
        for w in (QLabel("Période du"), self.du, QLabel("au"), self.au, self.btn):
            barre.addWidget(w)
        self.valeurs = {}
        cartes = QHBoxLayout()
        for titre in self.CARTES:
            cadre, self.valeurs[titre] = carte(titre)
            cartes.addWidget(cadre)
        self.canvas_retards, self.ax_retards = graphique()
        self.canvas_evolution, self.ax_evolution = graphique()
        graphiques = QVBoxLayout()
        graphiques.addWidget(self.canvas_retards)
        graphiques.addWidget(self.canvas_evolution)
        self.classement = tableau([("Rang", "rang"), ("Ligne", "nom"), ("Ponctualité (%)", "ponctualite"),
                                   ("Retard moyen (min)", "retard_moyen"), ("Incidents", "incidents")])
        self.anomalies = tableau([("Anomalie", "type"), ("Détail", "message")])
        colonne = QVBoxLayout()
        for titre, t in (("Classement des lignes (ponctualité)", self.classement), ("Anomalies détectées", self.anomalies)):
            groupe = QGroupBox(titre)
            QVBoxLayout(groupe).addWidget(t)
            colonne.addWidget(groupe)
        corps = QHBoxLayout()
        corps.addLayout(graphiques, 1)
        corps.addLayout(colonne, 1)
        self.pile.addLayout(barre)
        self.pile.addLayout(cartes)
        self.pile.addLayout(corps, 1)

    def periode(self):
        return lire_periode(self.du, self.au)

    def afficher(self, cartes, classement, anomalies, evolution):
        for titre, valeur in cartes.items():
            self.valeurs[titre].setText(valeur)
        remplir(self.classement, [dict(l, rang=i + 1, ponctualite=NC if l["ponctualite"] is None else l["ponctualite"],
                                       retard_moyen=NC if l["retard_moyen"] is None else l["retard_moyen"])
                                  for i, l in enumerate(classement)])
        remplir(self.anomalies, anomalies)
        # Graphique 1 : comparaison des retards moyens par ligne
        ax = self.ax_retards
        ax.clear()
        lignes = [l for l in classement if l["retard_moyen"] is not None]
        ax.bar([l["nom"] for l in lignes], [l["retard_moyen"] for l in lignes],
               color=[COULEURS["danger"] if l["retard_moyen"] > 15 else COULEURS["accent"] for l in lignes])
        ax.axhline(0, color=COULEURS["discret"], linewidth=0.8)
        habiller(self.canvas_retards, ax, "Retard moyen à l'arrivée par ligne (min)")
        # Graphique 2 : évolution du retard moyen et du nombre de trajets par jour
        ax = self.ax_evolution
        ax.clear()
        jours = [p["jour"] for p in evolution]
        ax.plot(jours, [float("nan") if p["retard_moyen"] is None else p["retard_moyen"] for p in evolution],
                color=COULEURS["accent"], marker="o", markersize=3, label="Retard moyen (min)")
        ax.bar(jours, [p["trajets"] for p in evolution], color=COULEURS["bleu"], alpha=0.35, label="Trajets / jour")
        ax.legend(fontsize=8, facecolor=COULEURS["panneau"], labelcolor=COULEURS["texte"])
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        habiller(self.canvas_evolution, ax, "Évolution dans le temps")


class PageAnalyse(Page):
    def __init__(self, libelles_seuils):
        super().__init__("Analyse des retards et détection des anomalies")
        self.du, self.au, self.ligne, self.btn = champ_jour(30), champ_jour(), QComboBox(), bouton("Calculer")
        barre = QHBoxLayout()
        for w in (QLabel("Période du"), self.du, QLabel("au"), self.au, self.ligne, self.btn):
            barre.addWidget(w)
        barre.addStretch()
        self.indicateurs = tableau([("Indicateur", "nom"), ("Valeur", "valeur")])
        self.lignes = tableau([("Ligne", "nom")] + COLONNES_STATS[1:])
        self.vehicules = tableau([("Véhicule", "nom")] + COLONNES_STATS[1:])
        self.anomalies = tableau([("Anomalie", "type"), ("Détail", "message")])
        self.seuils = {cle: QSpinBox() for cle in libelles_seuils}
        for spin in self.seuils.values():
            spin.setRange(0, 1000)
        self.btn_seuils = bouton("Enregistrer les seuils")
        form = formulaire("Seuils configurables", [(libelles_seuils[c], s) for c, s in self.seuils.items()], [self.btn_seuils])
        gauche = QVBoxLayout()
        gauche.addWidget(self.indicateurs, 3)
        gauche.addWidget(form, 2)
        droite = QVBoxLayout()
        for titre, t in (("Par ligne", self.lignes), ("Par véhicule", self.vehicules), ("Anomalies", self.anomalies)):
            groupe = QGroupBox(titre)
            QVBoxLayout(groupe).addWidget(t)
            droite.addWidget(groupe)
        corps = QHBoxLayout()
        corps.addLayout(gauche, 2)
        corps.addLayout(droite, 3)
        self.pile.addLayout(barre)
        self.pile.addLayout(corps, 1)

    def periode(self):
        return lire_periode(self.du, self.au)

    def afficher(self, indicateurs, par_ligne, par_vehicule, anomalies, seuils):
        remplir(self.indicateurs, indicateurs)
        remplir(self.lignes, par_ligne)
        remplir(self.vehicules, par_vehicule)
        remplir(self.anomalies, anomalies)
        for cle, valeur in seuils.items():
            self.seuils[cle].setValue(valeur)

    def lire_seuils(self):
        return {cle: spin.value() for cle, spin in self.seuils.items()}


class PageSimulation(Page):
    def __init__(self):
        super().__init__("Simulation de perturbations")
        bandeau = QLabel("SIMULATION : résultats fictifs, séparés de l'historique. Aucune donnée n'est modifiée.")
        bandeau.setObjectName("bandeau")
        self.vehicule, self.debut, self.fin = QComboBox(), champ_date(), champ_date()
        self.btn_vehicule = bouton("Simuler l'indisponibilité")
        self.minutes, self.ligne, self.du, self.au = QSpinBox(), QComboBox(), champ_jour(30), champ_jour()
        self.minutes.setRange(1, 240)
        self.minutes.setValue(10)
        self.btn_duree = bouton("Simuler l'allongement")
        self.resultat = QTextBrowser()
        colonne = QVBoxLayout()
        colonne.addWidget(formulaire("1. Indisponibilité d'un véhicule", [("Véhicule", self.vehicule), ("Du", self.debut),
                                                                          ("Au", self.fin)], [self.btn_vehicule]))
        colonne.addWidget(formulaire("2. Augmentation des durées de trajet", [("Minutes en plus", self.minutes),
                                                                              ("Ligne", self.ligne), ("Période du", self.du),
                                                                              ("au", self.au)], [self.btn_duree]))
        colonne.addStretch()
        corps = QHBoxLayout()
        corps.addLayout(colonne, 1)
        corps.addWidget(self.resultat, 2)
        self.pile.addWidget(bandeau)
        self.pile.addLayout(corps, 1)

    def lire(self):
        debut, fin = lire_periode(self.du, self.au)
        return {"id_vehicule": self.vehicule.currentData(), "debut": lire_date(self.debut), "fin": lire_date(self.fin),
                "minutes": self.minutes.value(), "id_ligne": self.ligne.currentData(), "periode": (debut, fin)}

    def afficher(self, titre, colonnes, lignes, resume, hypotheses):
        """Tableau HTML simple : colonnes = en-têtes, lignes = listes de textes."""
        entetes = "".join(f"<th>{c}</th>" for c in colonnes)
        corps = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in lignes)
        liste = "".join(f"<li>{h}</li>" for h in hypotheses)
        self.resultat.setHtml(f"<h2 style='color:{COULEURS['accent']}'>{titre}</h2><p>{resume}</p>"
                              f"<table cellpadding='6' border='1' style='border-collapse:collapse'><tr>{entetes}</tr>{corps}</table>"
                              f"<h3>Hypothèses</h3><ul>{liste}</ul>")
