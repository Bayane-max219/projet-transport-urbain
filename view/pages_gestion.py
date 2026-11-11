"""Pages de gestion : lignes, arrêts, véhicules, trajets, incidents (formulaires et tableaux seulement)."""
from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QVBoxLayout, QGroupBox

from view.widgets import (Page, bouton, champ_date, champ_jour, formulaire, lire_date, lire_periode, remplir,
                          remplir_combo, selection, tableau)


class PageLignes(Page):
    def __init__(self):
        super().__init__("Lignes de transport et ordre des arrêts")
        self.table = tableau([("Code", "code"), ("Nom", "nom"), ("Départ", "depart"), ("Arrivée", "arrivee"),
                              ("Statut", "statut")])
        self.code, self.nom, self.depart, self.arrivee, self.description = (QLineEdit() for _ in range(5))
        self.btn_creer, self.btn_modifier = bouton("Créer"), bouton("Modifier", "secondaire")
        self.btn_actif = bouton("Activer / Désactiver", "danger")
        form = formulaire("Ligne", [("Code", self.code), ("Nom", self.nom), ("Départ", self.depart),
                                    ("Arrivée", self.arrivee), ("Description", self.description)],
                          [self.btn_creer, self.btn_modifier, self.btn_actif])
        haut = QHBoxLayout()
        haut.addWidget(self.table, 3)
        haut.addWidget(form, 2)

        self.arrets = tableau([("Ordre", "ordre"), ("Arrêt", "nom"), ("Localisation", "localisation")])
        self.arret, self.ordre = QComboBox(), QSpinBox()
        self.ordre.setSpecialValueText("à la fin")
        self.ordre.setRange(0, 99)
        self.btn_associer, self.btn_retirer = bouton("Ajouter à la ligne"), bouton("Retirer de la ligne", "danger")
        bas = QHBoxLayout()
        bas.addWidget(self.arrets, 3)
        bas.addWidget(formulaire("Arrêts de la ligne sélectionnée", [("Arrêt", self.arret), ("Position", self.ordre)],
                                 [self.btn_associer, self.btn_retirer]), 2)
        self.pile.addLayout(haut, 3)
        self.pile.addLayout(bas, 2)
        self.table.itemSelectionChanged.connect(self._remplir_formulaire)

    def _remplir_formulaire(self):
        ligne = selection(self.table)
        if ligne:
            for champ, cle in ((self.code, "code"), (self.nom, "nom"), (self.depart, "depart"), (self.arrivee, "arrivee")):
                champ.setText(ligne[cle])
            self.description.setText(ligne["description"] or "")

    def selectionne(self):
        return selection(self.table)

    def afficher(self, lignes):
        remplir(self.table, [dict(l, statut="Active" if l["actif"] else "Inactive") for l in lignes])

    def lire(self):
        return {"code": self.code.text(), "nom": self.nom.text(), "depart": self.depart.text(),
                "arrivee": self.arrivee.text(), "description": self.description.text(),
                "id_arret": self.arret.currentData(), "ordre": self.ordre.value() or None}


class PageArrets(Page):
    def __init__(self):
        super().__init__("Arrêts")
        self.table = tableau([("Nom", "nom"), ("Localisation", "localisation"), ("Statut", "statut")])
        self.nom, self.localisation = QLineEdit(), QLineEdit()
        self.btn_creer, self.btn_modifier = bouton("Créer"), bouton("Modifier", "secondaire")
        self.btn_actif = bouton("Activer / Désactiver", "danger")
        colonne = QVBoxLayout()
        colonne.addWidget(formulaire("Arrêt", [("Nom", self.nom), ("Localisation fictive", self.localisation)],
                                     [self.btn_creer, self.btn_modifier, self.btn_actif]))
        colonne.addStretch()
        ligne = QHBoxLayout()
        ligne.addWidget(self.table, 3)
        ligne.addLayout(colonne, 1)
        self.pile.addLayout(ligne)
        self.table.itemSelectionChanged.connect(self._remplir_formulaire)

    def _remplir_formulaire(self):
        arret = selection(self.table)
        if arret:
            self.nom.setText(arret["nom"])
            self.localisation.setText(arret["localisation"] or "")

    def selectionne(self):
        return selection(self.table)

    def afficher(self, arrets):
        remplir(self.table, [dict(a, statut="Actif" if a["actif"] else "Inactif") for a in arrets])

    def lire(self):
        return {"nom": self.nom.text(), "localisation": self.localisation.text()}


class PageVehicules(Page):
    def __init__(self, statuts):
        super().__init__("Véhicules")
        self.table = tableau([("Immatriculation", "immatriculation"), ("Type", "type_vehicule"),
                              ("Capacité", "capacite"), ("Statut", "statut")])
        self.immat, self.type, self.capacite, self.statut = QLineEdit(), QLineEdit(), QSpinBox(), QComboBox()
        self.capacite.setRange(0, 500)
        self.capacite.setValue(30)
        remplir_combo(self.statut, [(s, s) for s in statuts])
        self.btn_creer, self.btn_modifier = bouton("Créer"), bouton("Modifier", "secondaire")
        self.btn_statut = bouton("Appliquer le statut")
        colonne = QVBoxLayout()
        colonne.addWidget(formulaire("Véhicule", [("Immatriculation", self.immat), ("Type", self.type),
                                                  ("Capacité", self.capacite)], [self.btn_creer, self.btn_modifier]))
        colonne.addWidget(formulaire("Statut du véhicule sélectionné", [("Statut", self.statut)], [self.btn_statut]))
        colonne.addStretch()
        ligne = QHBoxLayout()
        ligne.addWidget(self.table, 3)
        ligne.addLayout(colonne, 1)
        self.pile.addLayout(ligne)
        self.table.itemSelectionChanged.connect(self._remplir_formulaire)

    def _remplir_formulaire(self):
        v = selection(self.table)
        if v:
            self.immat.setText(v["immatriculation"])
            self.type.setText(v["type_vehicule"])
            self.capacite.setValue(v["capacite"])
            self.statut.setCurrentIndex(self.statut.findData(v["statut"]))

    def selectionne(self):
        return selection(self.table)

    def afficher(self, vehicules):
        remplir(self.table, vehicules)

    def lire(self):
        return {"immat": self.immat.text(), "type": self.type.text(), "capacite": self.capacite.value(),
                "statut": self.statut.currentData()}


class PageTrajets(Page):
    def __init__(self, statuts):
        super().__init__("Trajets : planification et suivi")
        self.du, self.au = champ_jour(7), champ_jour(-7)
        self.f_ligne, self.f_vehicule, self.f_statut = QComboBox(), QComboBox(), QComboBox()
        remplir_combo(self.f_statut, [(s, s) for s in statuts], tout="Tous les statuts")
        self.btn_filtrer = bouton("Filtrer")
        filtres = QHBoxLayout()
        for w in (QLabel("Du"), self.du, QLabel("au"), self.au, self.f_ligne, self.f_vehicule, self.f_statut, self.btn_filtrer):
            filtres.addWidget(w)
        self.table = tableau([("N°", "id_trajet"), ("Date", "date_trajet"), ("Ligne", "ligne"), ("Véhicule", "vehicule"),
                              ("Départ prévu", "depart_prevu"), ("Arrivée prévue", "arrivee_prevue"),
                              ("Départ réel", "depart_reel"), ("Arrivée réelle", "arrivee_reel"),
                              ("Retard arrivée (min)", "retard"), ("Statut", "statut")])

        self.ligne, self.vehicule = QComboBox(), QComboBox()
        self.depart_prevu, self.arrivee_prevue = champ_date(), champ_date()
        self.btn_planifier, self.btn_modifier = bouton("Planifier"), bouton("Modifier le trajet sélectionné", "secondaire")
        self.depart_reel, self.arrivee_reel = champ_date(), champ_date()
        for champ in (self.arrivee_prevue, self.arrivee_reel):  # valeur par défaut : 1 h après le départ
            champ.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.btn_reel = bouton("Enregistrer les heures réelles")
        self.btn_interrompre = bouton("Interrompre", "secondaire")
        self.btn_annuler = bouton("Annuler le trajet", "danger")
        bas = QHBoxLayout()
        bas.addWidget(formulaire("Planification", [("Ligne", self.ligne), ("Véhicule", self.vehicule),
                                                   ("Départ prévu", self.depart_prevu), ("Arrivée prévue", self.arrivee_prevue)],
                                 [self.btn_planifier, self.btn_modifier]))
        bas.addWidget(formulaire("Suivi du trajet sélectionné", [("Départ réel", self.depart_reel),
                                                                 ("Arrivée réelle", self.arrivee_reel)],
                                 [self.btn_reel, self.btn_interrompre, self.btn_annuler]))
        self.pile.addLayout(filtres)
        self.pile.addWidget(self.table, 1)
        self.pile.addLayout(bas)
        self.table.itemSelectionChanged.connect(self._remplir_formulaire)

    def _remplir_formulaire(self):
        t = selection(self.table)
        if t:
            self.ligne.setCurrentIndex(self.ligne.findData(t["id_ligne"]))
            self.vehicule.setCurrentIndex(self.vehicule.findData(t["id_vehicule"]))
            for champ, cle in ((self.depart_prevu, "depart_prevu"), (self.arrivee_prevue, "arrivee_prevue"),
                               (self.depart_reel, "depart_reel"), (self.arrivee_reel, "arrivee_reel")):
                if t[cle]:
                    champ.setDateTime(t[cle])

    def selectionne(self):
        return selection(self.table)

    def filtres(self):
        debut, fin = lire_periode(self.du, self.au)
        return debut, fin, self.f_ligne.currentData(), self.f_vehicule.currentData(), self.f_statut.currentData()

    def afficher(self, trajets):
        remplir(self.table, trajets)

    def lire(self):
        return {"id_ligne": self.ligne.currentData(), "id_vehicule": self.vehicule.currentData(),
                "depart_prevu": lire_date(self.depart_prevu), "arrivee_prevue": lire_date(self.arrivee_prevue),
                "depart_reel": lire_date(self.depart_reel), "arrivee_reel": lire_date(self.arrivee_reel)}


class PageIncidents(Page):
    def __init__(self, types, gravites):
        super().__init__("Incidents")
        self.f_type, self.du, self.au = QComboBox(), champ_jour(30), champ_jour()
        remplir_combo(self.f_type, [(t, t) for t in types], tout="Tous les types")
        self.btn_filtrer = bouton("Filtrer")
        filtres = QHBoxLayout()
        for w in (self.f_type, QLabel("du"), self.du, QLabel("au"), self.au, self.btn_filtrer):
            filtres.addWidget(w)
        self.table = tableau([("Date", "date_incident"), ("Ligne", "ligne"), ("Véhicule", "vehicule"),
                              ("Type", "type_incident"), ("Gravité", "gravite"), ("Durée (min)", "duree_min"),
                              ("Description", "description")])
        self.trajet, self.date, self.type, self.gravite = QComboBox(), champ_date(), QComboBox(), QComboBox()
        self.duree, self.description = QSpinBox(), QLineEdit()
        self.duree.setRange(0, 600)
        remplir_combo(self.type, [(t, t) for t in types])
        remplir_combo(self.gravite, [(g, g) for g in gravites])
        self.btn_ajouter = bouton("Enregistrer l'incident")
        self.par_ligne = tableau([("Ligne", "ligne"), ("Incidents", "n")])
        self.par_vehicule = tableau([("Véhicule", "vehicule"), ("Incidents", "n")])
        classements = QHBoxLayout()
        for titre, t in (("Incidents par ligne", self.par_ligne), ("Véhicules les plus concernés", self.par_vehicule)):
            groupe = QGroupBox(titre)
            QVBoxLayout(groupe).addWidget(t)
            classements.addWidget(groupe)
        bas = QHBoxLayout()
        bas.addWidget(formulaire("Nouvel incident", [("Trajet", self.trajet), ("Date et heure", self.date),
                                                     ("Type", self.type), ("Gravité", self.gravite),
                                                     ("Durée de perturbation (min)", self.duree),
                                                     ("Description", self.description)], [self.btn_ajouter]), 1)
        bas.addLayout(classements, 1)
        self.pile.addLayout(filtres)
        self.pile.addWidget(self.table, 1)
        self.pile.addLayout(bas)

    def filtres(self):
        debut, fin = lire_periode(self.du, self.au)
        return self.f_type.currentData(), debut, fin

    def afficher(self, incidents, par_ligne, par_vehicule):
        remplir(self.table, incidents)
        remplir(self.par_ligne, par_ligne)
        remplir(self.par_vehicule, par_vehicule)

    def lire(self):
        return {"id_trajet": self.trajet.currentData(), "date": lire_date(self.date), "type": self.type.currentData(),
                "gravite": self.gravite.currentData(), "duree": self.duree.value(), "description": self.description.text()}
