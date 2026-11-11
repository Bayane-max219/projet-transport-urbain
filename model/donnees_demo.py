"""Jeu de données fictives : 4 lignes, 12 arrêts, 6 véhicules, 34 trajets, 6 incidents.
Tout passe par les vraies méthodes du modèle : les règles métier s'appliquent aux données de démo."""
import random
from datetime import datetime, time, timedelta

from model.commun import ErreurMetier
from model.incidents import TYPES

ARRETS = ["Analakely", "Isotry", "Anosy", "67 Ha", "Behoririka", "Ankorondrano", "Ivandry", "Ambohimanarina",
          "Andohatapenaka", "Itaosy", "Ambatobe", "Ivato"]
LIGNES = [  # code, nom, durée prévue (min), arrêts dans l'ordre de passage
    ("L1", "Analakely - Ivato", 80, ["Analakely", "Behoririka", "Ankorondrano", "Ivandry", "Ivato"]),
    ("L2", "Itaosy - Analakely", 70, ["Itaosy", "Andohatapenaka", "67 Ha", "Isotry", "Analakely"]),
    ("L3", "Ambohimanarina - Anosy", 90, ["Ambohimanarina", "Ankorondrano", "Behoririka", "Analakely", "Anosy"]),
    ("L4", "Ambatobe - Itaosy", 100, ["Ambatobe", "Ivandry", "Ankorondrano", "67 Ha", "Itaosy"]),
]
VEHICULES = [("1001 TAA", "Bus", 60), ("1002 TAA", "Bus", 55), ("2001 TBB", "Minibus", 30),
             ("2002 TBB", "Minibus", 28), ("3001 TCC", "Taxi-be", 25), ("3002 TCC", "Taxi-be", 22)]


def reinitialiser(m, maintenant=None):
    """Vide la base, recrée les tables et insère la démo. Retourne les messages des opérations invalides refusées."""
    m.db.creer_tables()
    aujourdhui = datetime.combine((maintenant or datetime.now()).date(), time.min)
    hasard = random.Random(7)

    ids_arrets = {nom: m.arrets.creer(nom, f"Quartier {nom} (fictif)") for nom in ARRETS}
    lignes = []
    for code, nom, duree, arrets in LIGNES:
        lignes.append((m.lignes.creer(code, nom, arrets[0], arrets[-1], "Ligne fictive"), duree))
        for arret in arrets:
            m.arrets.associer(lignes[-1][0], ids_arrets[arret])
    vehicules = [m.vehicules.creer(*v) for v in VEHICULES]

    # --- 28 trajets passés (14 jours, 2 par jour : 07h et 13h) puis 6 trajets planifiés à venir ---
    realises = []
    for i in range(34):
        passe = i < 28
        jour = aujourdhui - timedelta(days=14 - i // 2) if passe else aujourdhui + timedelta(days=1 + (i - 28) // 2)
        depart = jour + timedelta(hours=7 + 6 * (i % 2), minutes=hasard.randint(0, 40))
        id_ligne, duree = lignes[i % 4]
        id_vehicule = vehicules[i % 5 if passe else i % 4]
        id_trajet = m.trajets.planifier(id_ligne, id_vehicule, depart, depart + timedelta(minutes=duree))
        if not passe:
            continue
        tirage = hasard.random()
        if tirage < 0.10:
            m.trajets.annuler(id_trajet)
        elif tirage < 0.18:
            m.trajets.interrompre(id_trajet, depart + timedelta(minutes=3))
        else:
            u = hasard.random()  # 55 % ponctuels, 30 % en retard, 15 % en gros retard
            retard = hasard.randint(-4, 9) if u < 0.55 else hasard.randint(11, 28) if u < 0.85 else hasard.randint(31, 55)
            depart_reel = depart + timedelta(minutes=hasard.randint(-2, max(2, retard // 2)))
            arrivee_reel = depart + timedelta(minutes=duree + retard)
            m.trajets.enregistrer_reel(id_trajet, depart_reel, arrivee_reel)
            realises.append((id_trajet, id_vehicule, retard, depart_reel))

    # --- incidents : les gros retards + 3 incidents sur le véhicule n°1 (anomalie 3) ---
    choisis = [r for r in realises if r[2] > 25][:6] + [r for r in realises if r[1] == vehicules[0]][:3]
    for k, (id_trajet, _, retard, depart_reel) in enumerate(dict.fromkeys(choisis)):
        gravite = "élevé" if retard > 30 else "moyen" if retard > 10 else "faible"
        m.incidents.ajouter(id_trajet, depart_reel + timedelta(minutes=20), TYPES[k % len(TYPES)],
                            "Incident fictif de démonstration", gravite, max(retard, 5))

    # --- statuts des véhicules (après la planification, pour garder un historique cohérent) ---
    m.vehicules.definir_statut(vehicules[2], "en service")
    m.vehicules.definir_statut(vehicules[4], "en maintenance")
    m.vehicules.definir_statut(vehicules[5], "indisponible")

    # --- tentatives invalides : toutes refusées ---
    futur = m.trajets.lister(statut="planifié")[0]
    debut = futur["depart_prevu"]
    tentatives = [
        lambda: m.trajets.planifier(lignes[0][0], futur["id_vehicule"], debut + timedelta(minutes=10),
                                    debut + timedelta(minutes=70)),                                        # conflit
        lambda: m.trajets.planifier(lignes[1][0], vehicules[4], debut + timedelta(days=5),
                                    debut + timedelta(days=5, hours=1)),                                   # véhicule en maintenance
        lambda: m.trajets.planifier(lignes[2][0], vehicules[0], debut + timedelta(days=6),
                                    debut + timedelta(days=6) - timedelta(minutes=30)),                    # arrivée avant départ
    ]
    refus = []
    for tentative in tentatives:
        try:
            tentative()
        except ErreurMetier as erreur:
            refus.append(str(erreur))
    return refus
