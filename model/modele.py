"""Façade du modèle : regroupe toutes les classes métier autour d'une même connexion."""
from model.analyse import Analyse
from model.anomalies import Anomalies
from model.db import BaseDeDonnees
from model.incidents import Incidents
from model.lignes import Arrets, Lignes
from model.parametres import Parametres
from model.simulation import Simulation
from model.trajets import Trajets
from model.vehicules import Vehicules


class Modele:
    def __init__(self, db=None):
        self.db = db or BaseDeDonnees()
        self.lignes, self.arrets, self.vehicules = Lignes(self.db), Arrets(self.db), Vehicules(self.db)
        self.trajets, self.incidents, self.parametres = Trajets(self.db), Incidents(self.db), Parametres(self.db)
        self.analyse = Analyse(self.trajets, self.incidents, self.parametres)
        self.anomalies = Anomalies(self.trajets, self.incidents, self.parametres)
        self.simulation = Simulation(self.db, self.trajets, self.parametres)
