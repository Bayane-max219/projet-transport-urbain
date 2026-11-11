"""Contrôleur : reçoit les actions de l'utilisateur, valide les saisies, appelle le modèle, met à jour la vue."""
from model import donnees_demo
from model.analyse import metriques
from model.commun import NON_CALCULABLE, ErreurMetier, formater
from view.widgets import remplir, remplir_combo


def exiger(valeur, message):
    """Validation d'une saisie : refuse une valeur vide."""
    if valeur is None or valeur == "":
        raise ValueError(message)
    return valeur


def presenter(stats):
    """Remplace les valeurs impossibles à calculer (None) par « Non calculable »."""
    return dict(stats, retard_moyen=formater(stats["retard_moyen"]), ponctualite=formater(stats["ponctualite"]))


class Controleur:
    def __init__(self, modele, vue):
        self.m, self.v = modele, vue
        self._connecter()
        self.rafraichir()

    # ---------- branchement des boutons ----------
    def _connecter(self):
        v = self.v
        v.btn_demo.clicked.connect(self.reinitialiser_demo)
        v.tableau_bord.btn.clicked.connect(self.maj_tableau_bord)
        v.lignes.btn_creer.clicked.connect(self.creer_ligne)
        v.lignes.btn_modifier.clicked.connect(self.modifier_ligne)
        v.lignes.btn_actif.clicked.connect(self.basculer_ligne)
        v.lignes.btn_associer.clicked.connect(self.associer_arret)
        v.lignes.btn_retirer.clicked.connect(self.retirer_arret)
        v.lignes.table.itemSelectionChanged.connect(self.maj_arrets_ligne)
        v.arrets.btn_creer.clicked.connect(self.creer_arret)
        v.arrets.btn_modifier.clicked.connect(self.modifier_arret)
        v.arrets.btn_actif.clicked.connect(self.basculer_arret)
        v.vehicules.btn_creer.clicked.connect(self.creer_vehicule)
        v.vehicules.btn_modifier.clicked.connect(self.modifier_vehicule)
        v.vehicules.btn_statut.clicked.connect(self.changer_statut)
        v.trajets.btn_filtrer.clicked.connect(self.maj_trajets)
        v.trajets.btn_planifier.clicked.connect(self.planifier)
        v.trajets.btn_modifier.clicked.connect(self.modifier_trajet)
        v.trajets.btn_reel.clicked.connect(self.enregistrer_reel)
        v.trajets.btn_interrompre.clicked.connect(self.interrompre)
        v.trajets.btn_annuler.clicked.connect(self.annuler)
        v.incidents.btn_filtrer.clicked.connect(self.maj_incidents)
        v.incidents.btn_ajouter.clicked.connect(self.ajouter_incident)
        v.analyse.btn.clicked.connect(self.maj_analyse)
        v.analyse.btn_seuils.clicked.connect(self.enregistrer_seuils)
        v.simulation.btn_vehicule.clicked.connect(self.simuler_vehicule)
        v.simulation.btn_duree.clicked.connect(self.simuler_durees)

    def executer(self, action, succes=""):
        """Exécute une action du modèle et gère toutes les erreurs au même endroit."""
        try:
            action()
        except ErreurMetier as erreur:
            self.v.erreur(f"{erreur.anomalie}\n\n{erreur}" if erreur.anomalie else str(erreur))
        except ValueError as erreur:
            self.v.erreur(str(erreur))
        except Exception as erreur:  # noqa : une erreur inattendue ne doit pas fermer l'application
            self.v.erreur(f"Erreur inattendue : {erreur}")
        else:
            if succes:
                self.v.info(succes)
            self.rafraichir()

    # ---------- actualisation de la vue ----------
    def rafraichir(self):
        m, v = self.m, self.v
        lignes, vehicules = m.lignes.lister(), m.vehicules.lister()
        arrets = m.arrets.lister()
        actives = [(f"{l['code']} - {l['nom']}", l["id_ligne"]) for l in lignes if l["actif"]]
        toutes = [(f"{l['code']} - {l['nom']}", l["id_ligne"]) for l in lignes]
        choix_vehicules = [(x["immatriculation"], x["id_vehicule"]) for x in vehicules]
        v.lignes.afficher(lignes)
        v.arrets.afficher(arrets)
        v.vehicules.afficher(vehicules)
        remplir_combo(v.lignes.arret, [(a["nom"], a["id_arret"]) for a in arrets if a["actif"]])
        remplir_combo(v.trajets.ligne, actives)
        remplir_combo(v.trajets.vehicule, choix_vehicules)
        remplir_combo(v.trajets.f_ligne, toutes, tout="Toutes les lignes")
        remplir_combo(v.trajets.f_vehicule, choix_vehicules, tout="Tous les véhicules")
        remplir_combo(v.analyse.ligne, toutes, tout="Toutes les lignes")
        remplir_combo(v.simulation.vehicule, choix_vehicules)
        remplir_combo(v.simulation.ligne, toutes, tout="Toutes les lignes")
        self.maj_arrets_ligne()
        self.maj_trajets()
        self.maj_incidents()
        self.maj_tableau_bord()
        self.maj_analyse()

    def maj_arrets_ligne(self):
        ligne = self.v.lignes.selectionne()
        remplir(self.v.lignes.arrets, self.m.arrets.de_la_ligne(ligne["id_ligne"]) if ligne else [])

    def maj_trajets(self):
        debut, fin, id_ligne, id_vehicule, statut = self.v.trajets.filtres()
        trajets = self.m.trajets.lister(debut, fin, id_ligne, id_vehicule, statut)
        for t in trajets:
            mesures = metriques(t)
            t["retard"] = mesures["retard_arrivee"] if mesures else None
        self.v.trajets.afficher(trajets)

    def maj_incidents(self):
        v = self.v.incidents
        type_incident, debut, fin = v.filtres()
        recents = self.m.trajets.lister()[:150]
        remplir_combo(v.trajet, [(f"n°{t['id_trajet']} - {t['ligne']} - {t['depart_prevu']:%d/%m %H:%M} ({t['vehicule']})",
                                  t["id_trajet"]) for t in recents if t["statut"] != "annulé"])
        v.afficher(self.m.incidents.lister(type_incident, debut, fin), self.m.incidents.par_ligne(debut, fin),
                   self.m.incidents.par_vehicule(debut, fin))

    def maj_tableau_bord(self):
        m, t = self.m, self.v.tableau_bord
        debut, fin = t.periode()
        r = m.analyse.resume(debut, fin)
        cartes = {"Lignes actives": len(m.lignes.lister(seulement_actives=True)),
                  "Véhicules disponibles": len(m.vehicules.lister("disponible")),
                  "Trajets réalisés": r["realises"], "Trajets annulés": r["annules"],
                  "Taux de ponctualité": formater(r["ponctualite"], " %"),
                  "Retard moyen": formater(r["retard_moyen"], " min"), "Incidents": r["incidents"]}
        classement = m.analyse.classement(m.analyse.par_ligne(debut, fin))
        t.afficher({k: str(x) for k, x in cartes.items()}, classement, m.anomalies.detecter(debut, fin),
                   m.analyse.evolution(debut, fin))

    def maj_analyse(self):
        m, a = self.m, self.v.analyse
        debut, fin = a.periode()
        r = m.analyse.resume(debut, fin, a.ligne.currentData())
        lignes = m.analyse.par_ligne(debut, fin)
        calculables = [l for l in lignes if l["ponctualite"] is not None]
        plus_ponctuelle = max(calculables, key=lambda l: l["ponctualite"], default=None)
        plus_en_retard = max(calculables, key=lambda l: l["retard_moyen"], default=None)
        valeurs = [("Trajets planifiés (à venir)", r["planifies"]), ("Trajets réalisés", r["realises"]),
                   ("Trajets annulés", r["annules"]), ("Trajets interrompus (exclus des moyennes)", r["interrompus"]),
                   ("Taux d'annulation", formater(r["taux_annulation"], " %")),
                   ("Trajets évaluables (réalisés, heures réelles valides)", r["evaluables"]),
                   ("Retard moyen à l'arrivée", formater(r["retard_moyen"], " min")),
                   ("Taux de ponctualité", formater(r["ponctualite"], " %")),
                   ("Nombre d'incidents", r["incidents"]),
                   ("Ligne la plus ponctuelle", plus_ponctuelle["nom"] if plus_ponctuelle else NON_CALCULABLE),
                   ("Ligne au retard moyen le plus élevé", plus_en_retard["nom"] if plus_en_retard else NON_CALCULABLE)]
        a.afficher([{"nom": n, "valeur": x} for n, x in valeurs], [presenter(l) for l in lignes],
                   [presenter(x) for x in m.analyse.par_vehicule(debut, fin)], m.anomalies.detecter(debut, fin),
                   m.parametres.tous())

    # ---------- lignes et arrêts ----------
    def creer_ligne(self):
        d = self.v.lignes.lire()
        self.executer(lambda: self.m.lignes.creer(d["code"], d["nom"], d["depart"], d["arrivee"], d["description"]),
                      "Ligne créée.")

    def modifier_ligne(self):
        d, ligne = self.v.lignes.lire(), self.v.lignes.selectionne()
        self.executer(lambda: self.m.lignes.modifier(exiger(ligne, "Sélectionnez une ligne.")["id_ligne"], d["code"],
                                                     d["nom"], d["depart"], d["arrivee"], d["description"]), "Ligne modifiée.")

    def basculer_ligne(self):
        ligne = self.v.lignes.selectionne()
        if not ligne:
            return self.v.erreur("Sélectionnez une ligne.")
        if ligne["actif"] and not self.v.confirmer(f"Désactiver la ligne {ligne['code']} ? Les trajets passés sont conservés."):
            return
        self.executer(lambda: self.m.lignes.definir_actif(ligne["id_ligne"], not ligne["actif"]), "Statut modifié.")

    def associer_arret(self):
        d, ligne = self.v.lignes.lire(), self.v.lignes.selectionne()
        self.executer(lambda: self.m.arrets.associer(exiger(ligne, "Sélectionnez une ligne.")["id_ligne"],
                                                     exiger(d["id_arret"], "Choisissez un arrêt."), d["ordre"]),
                      "Arrêt ajouté à la ligne.")

    def retirer_arret(self):
        ligne, arret = self.v.lignes.selectionne(), self.v.lignes.arrets.lignes
        choisi = arret[self.v.lignes.arrets.currentRow()] if self.v.lignes.arrets.currentRow() >= 0 else None
        self.executer(lambda: self.m.arrets.retirer(exiger(ligne, "Sélectionnez une ligne.")["id_ligne"],
                                                    exiger(choisi, "Sélectionnez un arrêt dans la liste de la ligne.")["id_arret"]),
                      "Arrêt retiré de la ligne.")

    def creer_arret(self):
        d = self.v.arrets.lire()
        self.executer(lambda: self.m.arrets.creer(d["nom"], d["localisation"]), "Arrêt créé.")

    def modifier_arret(self):
        d, arret = self.v.arrets.lire(), self.v.arrets.selectionne()
        self.executer(lambda: self.m.arrets.modifier(exiger(arret, "Sélectionnez un arrêt.")["id_arret"], d["nom"],
                                                     d["localisation"]), "Arrêt modifié.")

    def basculer_arret(self):
        arret = self.v.arrets.selectionne()
        self.executer(lambda: self.m.arrets.definir_actif(exiger(arret, "Sélectionnez un arrêt.")["id_arret"],
                                                          not arret["actif"]), "Statut modifié.")

    # ---------- véhicules ----------
    def creer_vehicule(self):
        d = self.v.vehicules.lire()
        self.executer(lambda: self.m.vehicules.creer(d["immat"], d["type"], d["capacite"]), "Véhicule créé.")

    def modifier_vehicule(self):
        d, vehicule = self.v.vehicules.lire(), self.v.vehicules.selectionne()
        self.executer(lambda: self.m.vehicules.modifier(exiger(vehicule, "Sélectionnez un véhicule.")["id_vehicule"],
                                                        d["immat"], d["type"], d["capacite"]), "Véhicule modifié.")

    def changer_statut(self):
        d, vehicule = self.v.vehicules.lire(), self.v.vehicules.selectionne()
        self.executer(lambda: self.m.vehicules.definir_statut(exiger(vehicule, "Sélectionnez un véhicule.")["id_vehicule"],
                                                              d["statut"]), "Statut modifié.")

    # ---------- trajets ----------
    def _trajet(self):
        return exiger(self.v.trajets.selectionne(), "Sélectionnez un trajet dans le tableau.")["id_trajet"]

    def planifier(self):
        d = self.v.trajets.lire()
        self.executer(lambda: self.m.trajets.planifier(exiger(d["id_ligne"], "Choisissez une ligne active."),
                                                       exiger(d["id_vehicule"], "Choisissez un véhicule."),
                                                       d["depart_prevu"], d["arrivee_prevue"]), "Trajet planifié.")

    def modifier_trajet(self):
        d = self.v.trajets.lire()
        self.executer(lambda: self.m.trajets.modifier(self._trajet(), exiger(d["id_ligne"], "Choisissez une ligne active."),
                                                      exiger(d["id_vehicule"], "Choisissez un véhicule."),
                                                      d["depart_prevu"], d["arrivee_prevue"]), "Trajet modifié.")

    def enregistrer_reel(self):
        d = self.v.trajets.lire()
        self.executer(lambda: self.m.trajets.enregistrer_reel(self._trajet(), d["depart_reel"], d["arrivee_reel"]),
                      "Heures réelles enregistrées : trajet réalisé.")

    def interrompre(self):
        d = self.v.trajets.lire()
        self.executer(lambda: self.m.trajets.interrompre(self._trajet(), d["depart_reel"]), "Trajet interrompu.")

    def annuler(self):
        if self.v.confirmer("Annuler ce trajet ? Il sera exclu des calculs de ponctualité."):
            self.executer(lambda: self.m.trajets.annuler(self._trajet()), "Trajet annulé.")

    # ---------- incidents, seuils ----------
    def ajouter_incident(self):
        d = self.v.incidents.lire()
        self.executer(lambda: self.m.incidents.ajouter(exiger(d["id_trajet"], "Choisissez un trajet."), d["date"],
                                                       d["type"], d["description"], d["gravite"], d["duree"]),
                      "Incident enregistré.")

    def enregistrer_seuils(self):
        def enregistrer():
            for cle, valeur in self.v.analyse.lire_seuils().items():
                self.m.parametres.definir(cle, valeur)
        self.executer(enregistrer, "Seuils enregistrés.")

    # ---------- simulations (lecture seule) ----------
    def simuler_vehicule(self):
        d = self.v.simulation.lire()
        try:
            if d["fin"] <= d["debut"]:
                raise ValueError("La fin de la période doit suivre son début.")
            r = self.m.simulation.indisponibilite_vehicule(exiger(d["id_vehicule"], "Choisissez un véhicule."),
                                                           d["debut"], d["fin"])
        except Exception as erreur:
            return self.v.erreur(str(erreur))
        lignes = [[t["trajet"], t["ligne"], f"{t['depart']:%Y-%m-%d %H:%M}", f"{t['arrivee']:%H:%M}",
                   t["remplacant"] or "<b>AUCUN : trajet non assuré</b>"] for t in r["trajets"]]
        resume = (f"Véhicule {r['vehicule']} indisponible : {len(lignes)} trajet(s) planifié(s) concerné(s), "
                  f"{r['sans_remplacant']} sans remplaçant.")
        self.v.simulation.afficher("Indisponibilité d'un véhicule", ["Trajet", "Ligne", "Départ", "Arrivée", "Remplaçant"],
                                   lignes, resume, r["hypotheses"])

    def simuler_durees(self):
        d = self.v.simulation.lire()
        r = self.m.simulation.augmentation_durees(d["minutes"], *d["periode"], d["id_ligne"])
        a, b = presenter(r["avant"]), presenter(r["apres"])
        lignes = [["Trajets évaluables", a["evaluables"], b["evaluables"]],
                  ["Retard moyen (min)", a["retard_moyen"], b["retard_moyen"]],
                  [f"Ponctualité (retard ≤ {r['seuil']} min, %)", a["ponctualite"], b["ponctualite"]]]
        self.v.simulation.afficher(f"Allongement fictif de {d['minutes']} minutes", ["Indicateur", "Historique (réel)", "Simulé (fictif)"],
                                   lignes, "Comparaison sur la période choisie.", r["hypotheses"])

    # ---------- données de démonstration ----------
    def reinitialiser_demo(self):
        if not self.v.confirmer("Toutes les données actuelles seront remplacées par les données de démonstration."):
            return
        self.executer(lambda: donnees_demo.reinitialiser(self.m), "Données de démonstration rechargées.")
