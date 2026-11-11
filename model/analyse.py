"""Module 6 : analyse des retards.

CONVENTIONS : tous les écarts sont en MINUTES ; positif = retard, négatif = avance.
 - un trajet est ÉVALUABLE s'il est « réalisé » avec des heures réelles valides (arrivée > départ) ;
 - les trajets annulés, interrompus ou incomplets sont EXCLUS des moyennes et de la ponctualité,
   mais comptés à part dans les statistiques ;
 - une valeur impossible à calculer (aucun trajet évaluable) vaut None, affichée « Non calculable ».
"""
from collections import defaultdict


def minutes(delta):
    return delta.total_seconds() / 60


def metriques(t):
    """Indicateurs d'un trajet, ou None s'il n'est pas évaluable."""
    if t["statut"] != "réalisé" or t["depart_reel"] is None or t["arrivee_reel"] is None \
            or t["arrivee_reel"] <= t["depart_reel"]:
        return None
    duree_reelle = minutes(t["arrivee_reel"] - t["depart_reel"])
    duree_prevue = minutes(t["arrivee_prevue"] - t["depart_prevu"])
    return {"retard_depart": minutes(t["depart_reel"] - t["depart_prevu"]),
            "retard_arrivee": minutes(t["arrivee_reel"] - t["arrivee_prevue"]),
            "duree_reelle": duree_reelle, "ecart_duree": duree_reelle - duree_prevue}


def statistiques(trajets, seuil_ponctualite):
    """Résumé d'une liste de trajets (lignes de la table trajets)."""
    mesures = [m for m in (metriques(t) for t in trajets) if m]
    ponctuels = sum(1 for m in mesures if m["retard_arrivee"] <= seuil_ponctualite)
    n = len(trajets)
    annules = sum(1 for t in trajets if t["statut"] == "annulé")
    return {
        "total": n,
        "planifies": sum(1 for t in trajets if t["statut"] == "planifié"),
        "realises": sum(1 for t in trajets if t["statut"] == "réalisé"),
        "annules": annules,
        "interrompus": sum(1 for t in trajets if t["statut"] == "interrompu"),
        "evaluables": len(mesures),
        "taux_annulation": annules / n * 100 if n else None,
        "retard_moyen": sum(m["retard_arrivee"] for m in mesures) / len(mesures) if mesures else None,
        "ponctualite": ponctuels / len(mesures) * 100 if mesures else None,
    }


class Analyse:
    def __init__(self, trajets, incidents, parametres):
        self.trajets, self.incidents, self.parametres = trajets, incidents, parametres

    def resume(self, debut, fin, id_ligne=None):
        lignes = self.trajets.lister(debut, fin, id_ligne)
        resume = statistiques(lignes, self.parametres.lire("seuil_ponctualite"))
        resume["incidents"] = self.incidents.compter(debut, fin)
        return resume

    def _grouper(self, debut, fin, cle):
        groupes = defaultdict(list)
        for t in self.trajets.lister(debut, fin):
            groupes[t[cle]].append(t)
        seuil = self.parametres.lire("seuil_ponctualite")
        return [dict(statistiques(ts, seuil), nom=nom) for nom, ts in sorted(groupes.items())]

    def par_ligne(self, debut, fin):
        """Statistiques de chaque ligne + nombre d'incidents."""
        incidents = {i["ligne"]: i["n"] for i in self.incidents.par_ligne(debut, fin)}
        return [dict(g, incidents=incidents.get(g["nom"], 0)) for g in self._grouper(debut, fin, "ligne")]

    def par_vehicule(self, debut, fin):
        return self._grouper(debut, fin, "vehicule")

    @staticmethod
    def classement(lignes):
        """Du plus ponctuel au moins ponctuel ; les « Non calculable » en dernier."""
        return sorted(lignes, key=lambda l: (l["ponctualite"] is None, -(l["ponctualite"] or 0)))

    def evolution(self, debut, fin):
        """Par jour : nombre de trajets (hors annulés) et retard moyen. Pour le graphique d'évolution."""
        jours = defaultdict(list)
        for t in self.trajets.lister(debut, fin):
            jours[t["date_trajet"]].append(t)
        seuil = self.parametres.lire("seuil_ponctualite")
        points = []
        for jour in sorted(jours):
            s = statistiques(jours[jour], seuil)
            points.append({"jour": jour, "trajets": s["total"] - s["annules"], "retard_moyen": s["retard_moyen"]})
        return points
