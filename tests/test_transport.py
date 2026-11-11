"""Tests obligatoires du cahier des charges + règles complémentaires.

Lancer (depuis projet_transport/) :  python -m unittest -v
Utilise une base séparée `transport_test` : la base de l'application n'est jamais touchée.
"""
import os
import unittest
from datetime import datetime, timedelta

os.environ.setdefault("DB_NAME", "transport_test")

from model.commun import CONFLIT, INCOHERENCE, RECURRENTS, RETARD, ErreurMetier, formater  # noqa: E402
from model.modele import Modele  # noqa: E402

JOUR = datetime(2026, 3, 10, 0, 0, 0)  # date fixe : les tests ne dépendent pas de l'heure d'exécution


def h(heure, minute=0):
    return JOUR + timedelta(hours=heure, minutes=minute)


class BaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = Modele()

    def setUp(self):
        m = self.m
        m.db.creer_tables()
        self.ligne = m.lignes.creer("L1", "Analakely - Ivato", "Analakely", "Ivato")
        self.bus = m.vehicules.creer("1001 TAA", "Bus", 60)
        self.bus2 = m.vehicules.creer("1002 TAA", "Bus", 55)

    def trajet_realise(self, depart, arrivee, depart_reel, arrivee_reel, vehicule=None):
        id_trajet = self.m.trajets.planifier(self.ligne, vehicule or self.bus, depart, arrivee)
        self.m.trajets.enregistrer_reel(id_trajet, depart_reel, arrivee_reel)
        return id_trajet

    def statut(self, id_trajet):
        return self.m.db.un("SELECT statut FROM trajets WHERE id_trajet = %s", (id_trajet,))["statut"]


class TestGestion(BaseTest):
    def test_ligne_code_unique(self):
        self.assertTrue(self.m.lignes.creer("L2", "Autre ligne", "A", "B"))

    def test_deux_lignes_meme_code(self):
        with self.assertRaises(ErreurMetier):
            self.m.lignes.creer("L1", "Doublon", "A", "B")

    def test_depart_et_arrivee_distincts(self):
        with self.assertRaises(ErreurMetier):
            self.m.lignes.creer("L9", "Boucle", "Isotry", "isotry")

    def test_vehicule_capacite_et_immatriculation(self):
        with self.assertRaises(ErreurMetier):
            self.m.vehicules.creer("X1", "Bus", 0)
        with self.assertRaises(ErreurMetier):
            self.m.vehicules.creer("1001 TAA", "Bus", 10)

    def test_ordre_des_arrets(self):
        ids = [self.m.arrets.creer(n) for n in ("A", "B", "C", "D")]
        for i in ids[:3]:
            self.m.arrets.associer(self.ligne, i)
        self.m.arrets.associer(self.ligne, ids[3], ordre=2)  # insertion au milieu
        noms = [a["nom"] for a in self.m.arrets.de_la_ligne(self.ligne)]
        self.assertEqual(noms, ["A", "D", "B", "C"])
        self.m.arrets.retirer(self.ligne, ids[0])
        self.assertEqual([a["ordre"] for a in self.m.arrets.de_la_ligne(self.ligne)], [1, 2, 3])
        with self.assertRaises(ErreurMetier):  # pas deux fois le même arrêt
            self.m.arrets.associer(self.ligne, ids[1])


class TestTrajets(BaseTest):
    def test_trajet_valide(self):
        id_trajet = self.m.trajets.planifier(self.ligne, self.bus, h(8), h(9, 30))
        self.assertEqual(self.statut(id_trajet), "planifié")

    def test_vehicule_indisponible(self):
        for statut in ("en maintenance", "indisponible"):
            self.m.vehicules.definir_statut(self.bus, statut)
            with self.assertRaises(ErreurMetier):
                self.m.trajets.planifier(self.ligne, self.bus, h(8), h(9))

    def test_chevauchement_meme_vehicule(self):
        self.m.trajets.planifier(self.ligne, self.bus, h(8), h(10))
        with self.assertRaises(ErreurMetier) as cm:
            self.m.trajets.planifier(self.ligne, self.bus, h(9), h(11))
        self.assertEqual(cm.exception.anomalie, CONFLIT)
        self.m.trajets.planifier(self.ligne, self.bus, h(10), h(11))  # bout à bout : autorisé
        self.m.trajets.planifier(self.ligne, self.bus2, h(9), h(11))  # autre véhicule : autorisé

    def test_trajet_annule_libere_le_vehicule(self):
        id_trajet = self.m.trajets.planifier(self.ligne, self.bus, h(8), h(10))
        self.m.trajets.annuler(id_trajet)
        self.m.trajets.planifier(self.ligne, self.bus, h(8), h(10))

    def test_arrivee_avant_depart(self):
        with self.assertRaises(ErreurMetier) as cm:
            self.m.trajets.planifier(self.ligne, self.bus, h(10), h(9))
        self.assertEqual(cm.exception.anomalie, INCOHERENCE)
        with self.assertRaises(ErreurMetier):  # 24 h ou plus : refusé
            self.m.trajets.planifier(self.ligne, self.bus, h(1), h(25))

    def test_ligne_desactivee(self):
        self.m.lignes.definir_actif(self.ligne, False)
        with self.assertRaises(ErreurMetier):
            self.m.trajets.planifier(self.ligne, self.bus, h(8), h(9))

    def test_seul_un_trajet_planifie_est_modifiable(self):
        id_trajet = self.trajet_realise(h(8), h(9), h(8), h(9))
        for action in (lambda: self.m.trajets.modifier(id_trajet, self.ligne, self.bus, h(10), h(11)),
                       lambda: self.m.trajets.annuler(id_trajet),
                       lambda: self.m.trajets.enregistrer_reel(id_trajet, h(8), h(9))):
            with self.assertRaises(ErreurMetier):
                action()

    def test_modifier_ne_entre_pas_en_conflit_avec_lui_meme(self):
        id_trajet = self.m.trajets.planifier(self.ligne, self.bus, h(8), h(10))
        self.m.trajets.modifier(id_trajet, self.ligne, self.bus, h(8, 30), h(10, 30))


class TestAnalyse(BaseTest):
    def test_retards_calcules(self):
        id_trajet = self.trajet_realise(h(8), h(9), h(8, 5), h(9, 20))  # prévu 60 min, réel 75 min
        t = self.m.trajets.lister()[0]
        from model.analyse import metriques
        m = metriques(t)
        self.assertEqual((m["retard_depart"], m["retard_arrivee"], m["duree_reelle"], m["ecart_duree"]), (5, 20, 75, 15))
        self.assertEqual(self.statut(id_trajet), "réalisé")

    def test_annule_et_interrompu_exclus_de_la_ponctualite(self):
        self.trajet_realise(h(8), h(9), h(8), h(9, 5))                      # ponctuel (5 min)
        self.trajet_realise(h(10), h(11), h(10), h(11, 30), self.bus2)      # en retard (30 min)
        self.m.trajets.annuler(self.m.trajets.planifier(self.ligne, self.bus, h(12), h(13)))
        self.m.trajets.interrompre(self.m.trajets.planifier(self.ligne, self.bus, h(14), h(15)), h(14, 2))
        s = self.m.analyse.resume(h(0), h(23))
        self.assertEqual((s["total"], s["evaluables"], s["annules"], s["interrompus"]), (4, 2, 1, 1))
        self.assertAlmostEqual(s["ponctualite"], 50.0)            # 1 ponctuel / 2 évaluables
        self.assertAlmostEqual(s["retard_moyen"], 17.5)
        self.assertAlmostEqual(s["taux_annulation"], 25.0)

    def test_seuil_de_ponctualite_configurable(self):
        self.trajet_realise(h(8), h(9), h(8), h(9, 15))  # 15 min de retard
        self.assertEqual(self.m.analyse.resume(h(0), h(23))["ponctualite"], 0.0)
        self.m.parametres.definir("seuil_ponctualite", 20)
        self.assertEqual(self.m.analyse.resume(h(0), h(23))["ponctualite"], 100.0)

    def test_base_sans_trajet(self):
        s = self.m.analyse.resume(h(0), h(23))
        self.assertEqual((s["total"], s["retard_moyen"], s["ponctualite"], s["taux_annulation"]), (0, None, None, None))
        self.assertEqual(formater(s["ponctualite"]), "Non calculable")
        self.assertEqual(self.m.analyse.evolution(h(0), h(23)), [])
        self.assertEqual(self.m.anomalies.detecter(h(0), h(23)), [])

    def test_retard_superieur_au_seuil(self):
        self.trajet_realise(h(8), h(9), h(8), h(9, 45))  # 45 min de retard > 30
        types = [a["type"] for a in self.m.anomalies.detecter(h(0), h(23))]
        self.assertIn(RETARD, types)

    def test_trois_incidents_sur_un_vehicule(self):
        ids = [self.trajet_realise(h(8 + 2 * i), h(9 + 2 * i), h(8 + 2 * i), h(9 + 2 * i)) for i in range(3)]
        for i in ids[:2]:
            self.m.incidents.ajouter(i, h(9), "embouteillage", "Test", "moyen", 10)
        self.assertNotIn(RECURRENTS, [a["type"] for a in self.m.anomalies.detecter(h(0), h(23))])
        self.m.incidents.ajouter(ids[2], h(9), "panne du véhicule", "Test", "élevé", 30)
        self.assertIn(RECURRENTS, [a["type"] for a in self.m.anomalies.detecter(h(0), h(23))])
        self.assertEqual(self.m.incidents.par_vehicule(h(0), h(23))[0]["n"], 3)


class TestSimulation(BaseTest):
    def test_simulation_sans_modification(self):
        self.m.trajets.planifier(self.ligne, self.bus, h(8), h(10))
        self.trajet_realise(h(12), h(13), h(12), h(13, 20))
        tables = ("lignes", "vehicules", "trajets", "incidents")
        instantane = lambda: [self.m.db.lire(f"SELECT * FROM {t}") for t in tables]
        avant = instantane()
        res = self.m.simulation.indisponibilite_vehicule(self.bus, h(0), h(23))
        self.m.simulation.augmentation_durees(30, h(0), h(23))
        self.assertEqual(instantane(), avant)
        self.assertEqual(len(res["trajets"]), 1)                       # seul le trajet planifié est concerné
        self.assertEqual(res["trajets"][0]["remplacant"], "1002 TAA")  # l'autre bus est libre

    def test_simulation_sans_remplacant(self):
        self.m.trajets.planifier(self.ligne, self.bus, h(8), h(10))
        self.m.trajets.planifier(self.ligne, self.bus2, h(8), h(10))
        res = self.m.simulation.indisponibilite_vehicule(self.bus, h(0), h(23))
        self.assertEqual(res["sans_remplacant"], 1)

    def test_augmentation_des_durees_degrade_la_ponctualite(self):
        self.trajet_realise(h(8), h(9), h(8), h(9, 5))
        res = self.m.simulation.augmentation_durees(10, h(0), h(23))
        self.assertEqual((res["avant"]["ponctualite"], res["apres"]["ponctualite"]), (100.0, 0.0))


if __name__ == "__main__":
    unittest.main()
