"""Module 4 : planification et suivi des trajets."""
from datetime import timedelta

from model.commun import CONFLIT, INCOHERENCE, ErreurMetier

INDISPONIBLES = ("en maintenance", "indisponible")  # statuts qui interdisent une nouvelle affectation


class Trajets:
    def __init__(self, db):
        self.db = db

    # ---------- règles ----------
    @staticmethod
    def _verifier_horaires(depart, arrivee, nom):
        if arrivee <= depart:
            raise ErreurMetier(f"{nom} : l'arrivée doit être postérieure au départ.", INCOHERENCE)
        if arrivee - depart >= timedelta(hours=24):
            raise ErreurMetier(f"{nom} : un trajet doit durer moins de 24 heures.", INCOHERENCE)

    def conflit(self, id_vehicule, depart, arrivee, sauf=0):
        """Trajet du véhicule qui chevauche [depart, arrivee] (les trajets annulés ne comptent pas), ou None."""
        return self.db.un("SELECT id_trajet, depart_prevu, arrivee_prevue FROM trajets WHERE id_vehicule = %s "
                          "AND statut <> 'annulé' AND id_trajet <> %s AND depart_prevu < %s AND arrivee_prevue > %s",
                          (id_vehicule, sauf, arrivee, depart))

    def _verifier_affectation(self, id_ligne, id_vehicule, depart, arrivee, sauf=0):
        """Toutes les règles de planification (appelé dans une transaction)."""
        ligne = self.db.un("SELECT actif FROM lignes WHERE id_ligne = %s", (id_ligne,))
        if not ligne:
            raise ErreurMetier("Ligne inexistante.")
        if not ligne["actif"]:
            raise ErreurMetier("Cette ligne est désactivée : aucun nouveau trajet possible.")
        vehicule = self.db.un("SELECT immatriculation, statut FROM vehicules WHERE id_vehicule = %s FOR UPDATE",
                              (id_vehicule,))
        if not vehicule:
            raise ErreurMetier("Véhicule inexistant.")
        if vehicule["statut"] in INDISPONIBLES:
            raise ErreurMetier(f"Le véhicule {vehicule['immatriculation']} est {vehicule['statut']} : affectation refusée.")
        self._verifier_horaires(depart, arrivee, "Horaires prévus")
        autre = self.conflit(id_vehicule, depart, arrivee, sauf)
        if autre:
            raise ErreurMetier(f"Conflit : {vehicule['immatriculation']} assure déjà le trajet n°{autre['id_trajet']} "
                               f"({autre['depart_prevu']:%H:%M}-{autre['arrivee_prevue']:%H:%M}).", CONFLIT)

    # ---------- opérations ----------
    def planifier(self, id_ligne, id_vehicule, depart, arrivee):
        with self.db.transaction():
            self._verifier_affectation(id_ligne, id_vehicule, depart, arrivee)
            return self.db.ecrire("INSERT INTO trajets (id_ligne, id_vehicule, depart_prevu, arrivee_prevue) "
                                  "VALUES (%s, %s, %s, %s)", (id_ligne, id_vehicule, depart, arrivee))

    def _planifie(self, id_trajet):
        trajet = self.db.un("SELECT * FROM trajets WHERE id_trajet = %s FOR UPDATE", (id_trajet,))
        if not trajet:
            raise ErreurMetier("Trajet inexistant.")
        if trajet["statut"] != "planifié":
            raise ErreurMetier(f"Le trajet est déjà {trajet['statut']} : opération impossible.")
        return trajet

    def modifier(self, id_trajet, id_ligne, id_vehicule, depart, arrivee):
        """Seul un trajet planifié peut être modifié."""
        with self.db.transaction():
            self._planifie(id_trajet)
            self._verifier_affectation(id_ligne, id_vehicule, depart, arrivee, sauf=id_trajet)
            self.db.ecrire("UPDATE trajets SET id_ligne=%s, id_vehicule=%s, depart_prevu=%s, arrivee_prevue=%s "
                           "WHERE id_trajet=%s", (id_ligne, id_vehicule, depart, arrivee, id_trajet))

    def enregistrer_reel(self, id_trajet, depart_reel, arrivee_reel):
        """Enregistre les heures réelles : le trajet devient « réalisé »."""
        with self.db.transaction():
            self._planifie(id_trajet)
            self._verifier_horaires(depart_reel, arrivee_reel, "Horaires réels")
            self.db.ecrire("UPDATE trajets SET depart_reel=%s, arrivee_reel=%s, statut='réalisé' WHERE id_trajet=%s",
                           (depart_reel, arrivee_reel, id_trajet))

    def annuler(self, id_trajet):
        with self.db.transaction():
            self._planifie(id_trajet)
            self.db.ecrire("UPDATE trajets SET statut='annulé' WHERE id_trajet=%s", (id_trajet,))

    def interrompre(self, id_trajet, depart_reel=None):
        with self.db.transaction():
            self._planifie(id_trajet)
            self.db.ecrire("UPDATE trajets SET statut='interrompu', depart_reel=%s WHERE id_trajet=%s",
                           (depart_reel, id_trajet))

    # ---------- consultation (l'historique est simplement la liste sans filtre) ----------
    def lister(self, debut=None, fin=None, id_ligne=None, id_vehicule=None, statut=None):
        sql = ("SELECT t.*, l.code AS ligne, l.nom AS nom_ligne, v.immatriculation AS vehicule "
               "FROM trajets t JOIN lignes l USING (id_ligne) JOIN vehicules v USING (id_vehicule) WHERE 1 = 1")
        params = []
        for condition, valeur in (("t.depart_prevu >= %s", debut), ("t.depart_prevu <= %s", fin),
                                  ("t.id_ligne = %s", id_ligne), ("t.id_vehicule = %s", id_vehicule),
                                  ("t.statut = %s", statut)):
            if valeur is not None:
                sql += f" AND {condition}"
                params.append(valeur)
        return self.db.lire(sql + " ORDER BY t.depart_prevu DESC", params)
