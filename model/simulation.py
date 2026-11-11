"""Module 9 : simulation de perturbations. LECTURE SEULE : aucune écriture en base.

Les résultats sont présentés séparément de l'historique, avec leurs hypothèses.
L'application ne prétend pas prévoir la circulation réelle.
"""
from datetime import timedelta

from model.analyse import statistiques
from model.trajets import INDISPONIBLES


class Simulation:
    def __init__(self, db, trajets, parametres):
        self.db, self.trajets, self.parametres = db, trajets, parametres

    def indisponibilite_vehicule(self, id_vehicule, debut, fin):
        """Trajets planifiés qui chevauchent la période d'indisponibilité, et véhicules de remplacement possibles."""
        vehicule = self.db.un("SELECT * FROM vehicules WHERE id_vehicule = %s", (id_vehicule,))
        concernes = [t for t in self.trajets.lister(id_vehicule=id_vehicule, statut="planifié")
                     if t["depart_prevu"] < fin and t["arrivee_prevue"] > debut]
        candidats = [v for v in self.db.lire("SELECT * FROM vehicules WHERE id_vehicule <> %s", (id_vehicule,))
                     if v["statut"] not in INDISPONIBLES]
        lignes = []
        for t in concernes:
            libres = [v for v in candidats if not self.trajets.conflit(v["id_vehicule"], t["depart_prevu"], t["arrivee_prevue"])]
            libres.sort(key=lambda v: abs(v["capacite"] - vehicule["capacite"]))  # capacité la plus proche d'abord
            lignes.append({"trajet": t["id_trajet"], "ligne": t["ligne"], "depart": t["depart_prevu"],
                           "arrivee": t["arrivee_prevue"],
                           "remplacant": libres[0]["immatriculation"] if libres else None})
        return {"vehicule": vehicule["immatriculation"], "trajets": lignes,
                "sans_remplacant": sum(1 for l in lignes if l["remplacant"] is None),
                "hypotheses": ["Seuls les trajets planifiés qui chevauchent la période sont concernés.",
                               "Un remplaçant doit être disponible ou en service, sans trajet qui chevauche.",
                               "Les trajets réalisés (historique) ne sont jamais touchés."]}

    def augmentation_durees(self, minutes_en_plus, debut, fin, id_ligne=None):
        """Effet fictif de +N minutes d'arrivée sur la ponctualité des trajets réalisés de la période."""
        reels = self.trajets.lister(debut, fin, id_ligne, statut="réalisé")
        simules = [dict(t, arrivee_reel=t["arrivee_reel"] + timedelta(minutes=minutes_en_plus))
                   if t["arrivee_reel"] else t for t in reels]
        seuil = self.parametres.lire("seuil_ponctualite")
        return {"avant": statistiques(reels, seuil), "apres": statistiques(simules, seuil), "seuil": seuil,
                "hypotheses": [f"Chaque trajet réalisé arrive {minutes_en_plus} min plus tard (perturbation uniforme fictive).",
                               "Le départ réel est inchangé ; la durée réelle augmente donc d'autant.",
                               "Ce n'est pas une prévision de la circulation réelle."]}
