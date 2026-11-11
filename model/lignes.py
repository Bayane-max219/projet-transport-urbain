"""Modules 1 et 2 : lignes, arrêts et ordre de passage."""
from model.commun import ErreurMetier


class Lignes:
    def __init__(self, db):
        self.db = db

    def _verifier(self, code, nom, depart, arrivee, id_ligne=0):
        if not all(x.strip() for x in (code, nom, depart, arrivee)):
            raise ErreurMetier("Code, nom, départ et arrivée sont obligatoires.")
        if depart.strip().lower() == arrivee.strip().lower():
            raise ErreurMetier("Le point de départ et le point d'arrivée doivent être distincts.")
        if self.db.un("SELECT 1 FROM lignes WHERE code = %s AND id_ligne <> %s", (code.strip(), id_ligne)):
            raise ErreurMetier(f"Le code de ligne {code.strip()} existe déjà.")

    def creer(self, code, nom, depart, arrivee, description=""):
        self._verifier(code, nom, depart, arrivee)
        return self.db.ecrire("INSERT INTO lignes (code, nom, depart, arrivee, description) VALUES (%s, %s, %s, %s, %s)",
                              (code.strip(), nom.strip(), depart.strip(), arrivee.strip(), description))

    def modifier(self, id_ligne, code, nom, depart, arrivee, description=""):
        self._verifier(code, nom, depart, arrivee, id_ligne)
        self.db.ecrire("UPDATE lignes SET code=%s, nom=%s, depart=%s, arrivee=%s, description=%s WHERE id_ligne=%s",
                       (code.strip(), nom.strip(), depart.strip(), arrivee.strip(), description, id_ligne))

    def definir_actif(self, id_ligne, actif):
        """Désactiver = actif 0. Jamais de suppression : les trajets historiques restent liés à la ligne."""
        self.db.ecrire("UPDATE lignes SET actif = %s WHERE id_ligne = %s", (int(actif), id_ligne))

    def lister(self, seulement_actives=False):
        filtre = "WHERE actif = 1" if seulement_actives else ""
        return self.db.lire(f"SELECT * FROM lignes {filtre} ORDER BY code")


class Arrets:
    def __init__(self, db):
        self.db = db

    def creer(self, nom, localisation=""):
        if not nom.strip():
            raise ErreurMetier("Le nom de l'arrêt est obligatoire.")
        if self.db.un("SELECT 1 FROM arrets WHERE nom = %s", (nom.strip(),)):
            raise ErreurMetier("Un arrêt portant ce nom existe déjà.")
        return self.db.ecrire("INSERT INTO arrets (nom, localisation) VALUES (%s, %s)", (nom.strip(), localisation))

    def modifier(self, id_arret, nom, localisation=""):
        if not nom.strip():
            raise ErreurMetier("Le nom de l'arrêt est obligatoire.")
        if self.db.un("SELECT 1 FROM arrets WHERE nom = %s AND id_arret <> %s", (nom.strip(), id_arret)):
            raise ErreurMetier("Un arrêt portant ce nom existe déjà.")
        self.db.ecrire("UPDATE arrets SET nom=%s, localisation=%s WHERE id_arret=%s", (nom.strip(), localisation, id_arret))

    def definir_actif(self, id_arret, actif):
        self.db.ecrire("UPDATE arrets SET actif = %s WHERE id_arret = %s", (int(actif), id_arret))

    def lister(self):
        return self.db.lire("SELECT * FROM arrets ORDER BY nom")

    # ---------- association ligne <-> arrêts (ordre de passage 1, 2, 3...) ----------
    def de_la_ligne(self, id_ligne):
        return self.db.lire("SELECT la.ordre, a.id_arret, a.nom, a.localisation FROM ligne_arrets la "
                            "JOIN arrets a USING (id_arret) WHERE la.id_ligne = %s ORDER BY la.ordre", (id_ligne,))

    def associer(self, id_ligne, id_arret, ordre=None):
        """Ajoute l'arrêt à la ligne à la position `ordre` (par défaut : à la fin). Les ordres restent 1..n."""
        with self.db.transaction():
            arret = self.db.un("SELECT actif FROM arrets WHERE id_arret = %s", (id_arret,))
            if not arret or not arret["actif"]:
                raise ErreurMetier("Arrêt inexistant ou inactif.")
            if self.db.un("SELECT 1 FROM ligne_arrets WHERE id_ligne = %s AND id_arret = %s", (id_ligne, id_arret)):
                raise ErreurMetier("Cet arrêt est déjà sur la ligne (les boucles ne sont pas prises en charge).")
            fin = self.db.un("SELECT COALESCE(MAX(ordre), 0) + 1 AS n FROM ligne_arrets WHERE id_ligne = %s", (id_ligne,))["n"]
            ordre = fin if ordre is None else ordre
            if not 1 <= ordre <= fin:
                raise ErreurMetier(f"L'ordre doit être compris entre 1 et {fin}.")
            self.db.ecrire("UPDATE ligne_arrets SET ordre = ordre + 1 WHERE id_ligne = %s AND ordre >= %s "
                           "ORDER BY ordre DESC", (id_ligne, ordre))  # fait de la place sans doublon d'ordre
            self.db.ecrire("INSERT INTO ligne_arrets (id_ligne, id_arret, ordre) VALUES (%s, %s, %s)",
                           (id_ligne, id_arret, ordre))

    def retirer(self, id_ligne, id_arret):
        with self.db.transaction():
            ligne = self.db.un("SELECT ordre FROM ligne_arrets WHERE id_ligne = %s AND id_arret = %s", (id_ligne, id_arret))
            if not ligne:
                raise ErreurMetier("Cet arrêt n'est pas sur la ligne.")
            self.db.ecrire("DELETE FROM ligne_arrets WHERE id_ligne = %s AND id_arret = %s", (id_ligne, id_arret))
            self.db.ecrire("UPDATE ligne_arrets SET ordre = ordre - 1 WHERE id_ligne = %s AND ordre > %s "
                           "ORDER BY ordre ASC", (id_ligne, ligne["ordre"]))  # referme le trou
