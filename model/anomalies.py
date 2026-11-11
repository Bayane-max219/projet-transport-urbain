"""Module 7 : détection des anomalies.

Les anomalies 4 (conflit d'affectation) et 5 (incohérence temporelle) sont des REFUS faits à la
planification (voir trajets.py). Ici : les anomalies 1, 2 et 3, calculées sur une période.

JUSTIFICATION DES SEUILS PAR DÉFAUT (modifiables dans l'application) :
 - 20 min d'écart de durée : au-delà, le trajet a duré nettement plus que prévu (embouteillage, panne) ;
 - 30 min de retard à l'arrivée : seuil à partir duquel un usager rate généralement sa correspondance ;
 - 3 incidents par véhicule sur la période : un seul incident est fortuit, trois suggèrent un problème de fond.
"""
from model.analyse import metriques
from model.commun import RECURRENTS, RETARD, TROP_LONG


class Anomalies:
    def __init__(self, trajets, incidents, parametres):
        self.trajets, self.incidents, self.parametres = trajets, incidents, parametres

    def detecter(self, debut, fin):
        """Retourne [{type, message}] pour la période [debut, fin]."""
        p = self.parametres.tous()
        trouvees = []
        for t in self.trajets.lister(debut, fin):
            m = metriques(t)
            if not m:
                continue
            lieu = f"Trajet n°{t['id_trajet']} (ligne {t['ligne']}, {t['vehicule']}, {t['depart_prevu']:%Y-%m-%d %H:%M})"
            if m["ecart_duree"] > p["seuil_ecart_duree"]:
                trouvees.append({"type": TROP_LONG, "message": f"{lieu} : {m['ecart_duree']:.0f} min de plus que prévu "
                                                               f"(seuil {p['seuil_ecart_duree']} min)."})
            if m["retard_arrivee"] > p["seuil_retard"]:
                trouvees.append({"type": RETARD, "message": f"{lieu} : arrivé avec {m['retard_arrivee']:.0f} min de "
                                                            f"retard (seuil {p['seuil_retard']} min)."})
        for v in self.incidents.par_vehicule(debut, fin):
            if v["n"] >= p["seuil_incidents"]:
                trouvees.append({"type": RECURRENTS, "message": f"Véhicule {v['vehicule']} : {v['n']} incidents sur la "
                                                                f"période (seuil {p['seuil_incidents']})."})
        return trouvees
