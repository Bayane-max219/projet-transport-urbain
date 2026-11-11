"""Fenêtre principale : onglets en haut (une page par module)."""
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from model.incidents import GRAVITES, TYPES
from model.parametres import LIBELLES
from model.vehicules import STATUTS
from view.pages_analyse import PageAnalyse, PageSimulation, PageTableauBord
from view.pages_gestion import PageArrets, PageIncidents, PageLignes, PageTrajets, PageVehicules
from view.style import FEUILLE
from view.widgets import bouton

STATUTS_TRAJET = ["planifié", "réalisé", "annulé", "interrompu"]


class Fenetre(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analyse et gestion des transports urbains (données fictives)")
        self.resize(1366, 800)
        self.setStyleSheet(FEUILLE)
        self.tableau_bord, self.lignes, self.arrets = PageTableauBord(), PageLignes(), PageArrets()
        self.vehicules, self.trajets = PageVehicules(STATUTS), PageTrajets(STATUTS_TRAJET)
        self.incidents, self.analyse = PageIncidents(TYPES, GRAVITES), PageAnalyse(LIBELLES)
        self.simulation = PageSimulation()
        self.onglets = QTabWidget()
        for nom, page in (("Tableau de bord", self.tableau_bord), ("Lignes", self.lignes), ("Arrêts", self.arrets),
                          ("Véhicules", self.vehicules), ("Trajets", self.trajets), ("Incidents", self.incidents),
                          ("Analyse", self.analyse), ("Simulation", self.simulation)):
            self.onglets.addTab(page, nom)
        self.btn_demo = bouton("Réinitialiser la démo", "secondaire")
        self.onglets.setCornerWidget(self.btn_demo)
        self.setCentralWidget(self.onglets)

    # messages (la vue affiche, le contrôleur décide)
    def info(self, message):
        self.statusBar().showMessage(message, 6000)

    def erreur(self, message):
        QMessageBox.warning(self, "Opération refusée", message)

    def confirmer(self, message):
        return QMessageBox.question(self, "Confirmation", message) == QMessageBox.Yes
