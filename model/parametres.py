"""Seuils configurables (table parametres)."""
from model.commun import ErreurMetier

LIBELLES = {"seuil_ponctualite": "Seuil de ponctualité (retard max. en min)",
            "seuil_ecart_duree": "Anomalie 1 : écart de durée max. (min)",
            "seuil_retard": "Anomalie 2 : retard à l'arrivée max. (min)",
            "seuil_incidents": "Anomalie 3 : nombre d'incidents par véhicule"}


class Parametres:
    def __init__(self, db):
        self.db = db

    def tous(self):
        return {l["cle"]: l["valeur"] for l in self.db.lire("SELECT * FROM parametres")}

    def lire(self, cle):
        return self.tous()[cle]

    def definir(self, cle, valeur):
        if cle not in LIBELLES or valeur < 0:
            raise ErreurMetier("Paramètre invalide (la valeur doit être positive).")
        self.db.ecrire("UPDATE parametres SET valeur = %s WHERE cle = %s", (valeur, cle))
