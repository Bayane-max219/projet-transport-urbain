-- Schéma MySQL du projet "Transports urbains" (dates : AAAA-MM-JJ HH:MM:SS)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS incidents, trajets, ligne_arrets, vehicules, arrets, lignes, parametres;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE lignes (
    id_ligne    INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(10) NOT NULL UNIQUE,
    nom         VARCHAR(100) NOT NULL,
    depart      VARCHAR(100) NOT NULL,
    arrivee     VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    actif       TINYINT NOT NULL DEFAULT 1,
    CHECK (actif IN (0, 1))
);

CREATE TABLE arrets (
    id_arret    INT AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL UNIQUE,
    localisation VARCHAR(150) NULL,
    actif       TINYINT NOT NULL DEFAULT 1,
    CHECK (actif IN (0, 1))
);

-- Un arrêt peut servir plusieurs lignes ; (id_ligne, id_arret) unique = pas de doublon sur une ligne
CREATE TABLE ligne_arrets (
    id_ligne INT NOT NULL,
    id_arret INT NOT NULL,
    ordre    INT NOT NULL,
    PRIMARY KEY (id_ligne, id_arret),
    UNIQUE (id_ligne, ordre),
    FOREIGN KEY (id_ligne) REFERENCES lignes (id_ligne),
    FOREIGN KEY (id_arret) REFERENCES arrets (id_arret),
    CHECK (ordre > 0)
);

CREATE TABLE vehicules (
    id_vehicule     INT AUTO_INCREMENT PRIMARY KEY,
    immatriculation VARCHAR(20) NOT NULL UNIQUE,
    type_vehicule   VARCHAR(30) NOT NULL,
    capacite        INT NOT NULL,
    statut          VARCHAR(20) NOT NULL DEFAULT 'disponible',
    CHECK (capacite > 0),
    CHECK (statut IN ('disponible', 'en service', 'en maintenance', 'indisponible'))
);

CREATE TABLE trajets (
    id_trajet      INT AUTO_INCREMENT PRIMARY KEY,
    id_ligne       INT NOT NULL,
    id_vehicule    INT NOT NULL,
    depart_prevu   DATETIME NOT NULL,
    arrivee_prevue DATETIME NOT NULL,
    depart_reel    DATETIME NULL,
    arrivee_reel   DATETIME NULL,
    statut         VARCHAR(15) NOT NULL DEFAULT 'planifié',
    date_trajet    DATE GENERATED ALWAYS AS (DATE(depart_prevu)) STORED,  -- la "date" du trajet
    FOREIGN KEY (id_ligne) REFERENCES lignes (id_ligne),
    FOREIGN KEY (id_vehicule) REFERENCES vehicules (id_vehicule),
    CHECK (arrivee_prevue > depart_prevu),
    CHECK (statut IN ('planifié', 'réalisé', 'annulé', 'interrompu'))
);

CREATE TABLE incidents (
    id_incident   INT AUTO_INCREMENT PRIMARY KEY,
    id_trajet     INT NOT NULL,
    date_incident DATETIME NOT NULL,
    type_incident VARCHAR(30) NOT NULL,
    description   VARCHAR(255) NOT NULL,
    gravite       VARCHAR(10) NOT NULL,
    duree_min     INT NOT NULL,
    FOREIGN KEY (id_trajet) REFERENCES trajets (id_trajet),
    CHECK (gravite IN ('faible', 'moyen', 'élevé')),
    CHECK (duree_min >= 0)
);

-- Table ajoutée : seuils configurables (ponctualité, anomalies)
CREATE TABLE parametres (
    cle    VARCHAR(50) PRIMARY KEY,
    valeur INT NOT NULL
);
INSERT INTO parametres VALUES ('seuil_ponctualite', 10), ('seuil_ecart_duree', 20), ('seuil_retard', 30),
                              ('seuil_incidents', 3);
