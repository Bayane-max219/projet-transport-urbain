"""Module 3 : véhicules."""
from model.commun import ErreurMetier

STATUTS = ["disponible", "en service", "en maintenance", "indisponible"]


class Vehicules:
    def __init__(self, db):
        self.db = db

    def _verifier(self, immatriculation, type_vehicule, capacite, id_vehicule=0):
        if not immatriculation.strip() or not type_vehicule.strip():
            raise ErreurMetier("L'immatriculation et le type sont obligatoires.")
        if capacite <= 0:
            raise ErreurMetier("La capacité doit être strictement positive.")
        if self.db.un("SELECT 1 FROM vehicules WHERE immatriculation = %s AND id_vehicule <> %s",
                      (immatriculation.strip(), id_vehicule)):
            raise ErreurMetier("Cette immatriculation existe déjà.")

    def creer(self, immatriculation, type_vehicule, capacite, statut="disponible"):
        self._verifier(immatriculation, type_vehicule, capacite)
        return self.db.ecrire("INSERT INTO vehicules (immatriculation, type_vehicule, capacite, statut) "
                              "VALUES (%s, %s, %s, %s)", (immatriculation.strip(), type_vehicule.strip(), capacite, statut))

    def modifier(self, id_vehicule, immatriculation, type_vehicule, capacite):
        self._verifier(immatriculation, type_vehicule, capacite, id_vehicule)
        self.db.ecrire("UPDATE vehicules SET immatriculation=%s, type_vehicule=%s, capacite=%s WHERE id_vehicule=%s",
                       (immatriculation.strip(), type_vehicule.strip(), capacite, id_vehicule))

    def definir_statut(self, id_vehicule, statut):
        if statut not in STATUTS:
            raise ErreurMetier("Statut inconnu.")
        self.db.ecrire("UPDATE vehicules SET statut = %s WHERE id_vehicule = %s", (statut, id_vehicule))

    def lister(self, statut=None):
        sql, params = "SELECT * FROM vehicules", ()
        if statut:
            sql, params = sql + " WHERE statut = %s", (statut,)
        return self.db.lire(sql + " ORDER BY immatriculation", params)
