import sqlite3, os, logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'app.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS taches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            contenu TEXT DEFAULT '',
            statut TEXT DEFAULT 'nouveau',
            important INTEGER DEFAULT 0,
            date_echeance TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            libelle TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT DEFAULT 'autre',
            date_depense TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS recettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            libelle TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT DEFAULT 'cotisation',
            date_recette TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS evenements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT,
            lieu TEXT,
            statut TEXT DEFAULT 'planification',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS evenement_creneaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evenement_id INTEGER NOT NULL,
            date_heure TEXT NOT NULL,
            FOREIGN KEY (evenement_id) REFERENCES evenements(id)
        );
        CREATE TABLE IF NOT EXISTS evenement_disponibilites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creneau_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            disponible INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creneau_id) REFERENCES evenement_creneaux(id)
        );
        CREATE TABLE IF NOT EXISTS kermesse_editions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            date_kermesse TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS kermesse_stands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edition_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            description TEXT,
            capacite INTEGER DEFAULT 2,
            FOREIGN KEY (edition_id) REFERENCES kermesse_editions(id)
        );
        CREATE TABLE IF NOT EXISTS kermesse_inscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stand_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            creneau TEXT DEFAULT 'journee',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stand_id) REFERENCES kermesse_stands(id)
        );
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            niveau TEXT,
            annee_scolaire TEXT DEFAULT '2025-2026',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prenom TEXT NOT NULL,
            nom TEXT NOT NULL,
            email TEXT,
            telephone TEXT,
            classe_id INTEGER,
            annee_scolaire TEXT DEFAULT '2025-2026',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (classe_id) REFERENCES classes(id)
        );
    """)
    db.commit()
    db.close()
    logger.info("[DB] Base initialisee")
