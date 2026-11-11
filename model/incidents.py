"""Module 5 : incidents."""
from model.commun import ErreurMetier

TYPES = ["embouteillage", "panne du véhicule", "difficulté de circulation", "arrêt prolongé", "autre incident"]
GRAVITES = ["faible", "moyen", "élevé"]


class Incidents:
    def __init__(self, db):
        self.db = db

    def ajouter(self, id_trajet, date, type_incident, description, gravite, duree_min):
        if type_incident not in TYPES or gravite not in GRAVITES:
            raise ErreurMetier("Type ou gravité invalide.")
        if not description.strip():
            raise ErreurMetier("La description est obligatoire.")
        if duree_min < 0:
            raise ErreurMetier("La durée de perturbation ne peut pas être négative.")
        if not self.db.un("SELECT 1 FROM trajets WHERE id_trajet = %s", (id_trajet,)):
            raise ErreurMetier("Trajet inexistant.")
        return self.db.ecrire("INSERT INTO incidents (id_trajet, date_incident, type_incident, description, gravite, "
                              "duree_min) VALUES (%s, %s, %s, %s, %s, %s)",
                              (id_trajet, date, type_incident, description.strip(), gravite, duree_min))

    def lister(self, type_incident=None, debut=None, fin=None):
        sql = ("SELECT i.*, l.code AS ligne, v.immatriculation AS vehicule FROM incidents i "
               "JOIN trajets t USING (id_trajet) JOIN lignes l USING (id_ligne) JOIN vehicules v USING (id_vehicule) "
               "WHERE 1 = 1")
        params = []
        for condition, valeur in (("i.type_incident = %s", type_incident), ("i.date_incident >= %s", debut),
                                  ("i.date_incident <= %s", fin)):
            if valeur is not None:
                sql += f" AND {condition}"
                params.append(valeur)
        return self.db.lire(sql + " ORDER BY i.date_incident DESC", params)

    def par_ligne(self, debut, fin):
        return self.db.lire("SELECT l.code AS ligne, COUNT(*) AS n FROM incidents i JOIN trajets t USING (id_trajet) "
                            "JOIN lignes l USING (id_ligne) WHERE i.date_incident BETWEEN %s AND %s "
                            "GROUP BY l.code ORDER BY n DESC", (debut, fin))

    def par_vehicule(self, debut, fin):
        """Véhicules classés par nombre d'incidents (les plus fréquemment concernés en premier)."""
        return self.db.lire("SELECT v.id_vehicule, v.immatriculation AS vehicule, COUNT(*) AS n FROM incidents i "
                            "JOIN trajets t USING (id_trajet) JOIN vehicules v USING (id_vehicule) "
                            "WHERE i.date_incident BETWEEN %s AND %s GROUP BY v.id_vehicule, v.immatriculation "
                            "ORDER BY n DESC", (debut, fin))

    def compter(self, debut, fin):
        return self.db.un("SELECT COUNT(*) AS n FROM incidents WHERE date_incident BETWEEN %s AND %s", (debut, fin))["n"]
