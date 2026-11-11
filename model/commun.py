"""Éléments partagés : exception métier, types d'anomalies, formatage."""

TROP_LONG = "Anomalie 1 - Trajet anormalement long"
RETARD = "Anomalie 2 - Retard important"
RECURRENTS = "Anomalie 3 - Incidents récurrents"
CONFLIT = "Anomalie 4 - Conflit d'affectation"
INCOHERENCE = "Anomalie 5 - Incohérence temporelle"

NON_CALCULABLE = "Non calculable"


class ErreurMetier(Exception):
    """Une règle métier est violée. `anomalie` : type d'anomalie (facultatif)."""

    def __init__(self, message, anomalie=None):
        super().__init__(message)
        self.anomalie = anomalie


def formater(valeur, unite=""):
    """Nombre -> texte ; None -> « Non calculable » (aucune division par zéro nulle part)."""
    return NON_CALCULABLE if valeur is None else f"{valeur:.1f}{unite}"
