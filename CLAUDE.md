# Parentix — CLAUDE.md

Application Flask déployée via **Projectix** pour piloter l'association de parents d'élèves **FCPE**.

---

## Contexte métier

L'application centralise les outils de pilotage de l'association :

- **Tâches** — suivi des actions de l'asso avec statuts (Nouveau / En cours / Clos), priorité, échéance, description rich-text. Affiché en résumé sur l'accueil.
- **Dépenses** — saisie des dépenses (libellé, montant, catégorie, date, notes). Catégories paramétrables.
- **Recettes** — saisie des recettes (libellé, montant, catégorie, date, notes). Catégories paramétrables.
- **Événements** — module style Doodle : créer un événement, proposer des créneaux (date + heure à la demi-heure), les participants saisissent leur nom et cochent leurs disponibilités. Grille récapitulative + timeline sur l'accueil.
- **Kermesse** — module dédié à l'organisation de la fête scolaire : éditions, stands avec capacité, inscriptions des bénévoles (nom + créneau matin/après-midi/journée). Auto-inscription rapide depuis la page détail.
- **Paramètres** — gestion des classes par année scolaire, annuaire des parents (prénom, nom, email, téléphone, classe), et configuration des catégories de dépenses/recettes.

---

## Stack technique

- **Python 3.12 / Flask** — `app.py` à la racine
- **Jinja2** — templates dans `templates/`
- **SQLite** — `data/app.db` (UNIQUEMENT, pas de JSON/CSV)
- **CSS déporté** — `static/css/style.css` (pas de styles inline sauf couleurs dynamiques de badges)
- **JS** — `static/js/app.js`

## Variables de config (en haut de app.py — ne pas supprimer)

```python
APP_NAME    = "Parentix"
APP_SLUG    = "parentix"
APP_RELEASE = "v1.0"          # INCRÉMENTER à chaque livraison
APP_DESCRIPTION = "Pilotage de l'association FCPE : taches, depenses, recettes, evenements, kermesse"
APP_ICON    = "🏫"
APP_COLOR   = "#1e40af"
APP_CATEGORY = ""
```

## Authentification

Identifiants définis dans `app.py` :

```python
USERS = {"admin": "parentix"}
```

Toutes les routes sont protégées par `require_login()` sauf `/login`, `/logout`, `/health`, `/static`, `/sw.js`.

---

## Routes existantes

| Route | Description |
|---|---|
| `/` | Dashboard principal |
| `/taches` | Gestion des tâches |
| `/depenses` | Suivi des dépenses |
| `/recettes` | Suivi des recettes |
| `/evenements` | Liste des événements (sondage dispo) |
| `/evenements/<id>` | Détail d'un événement — grille doodle |
| `/kermesse` | Liste des éditions de kermesse |
| `/kermesse/<id>` | Détail d'une kermesse — stands + inscriptions |
| `/parametres` | Classes, parents, catégories |
| `/health` | Healthcheck Projectix (obligatoire) |

## Routes API

### Tâches
- `POST /api/taches` — créer
- `PUT /api/taches/<id>` — modifier
- `DELETE /api/taches/<id>` — supprimer
- `PUT /api/taches/<id>/statut` — changer statut
- `PUT /api/taches/<id>/important` — toggle priorité

### Dépenses / Recettes
- `POST /api/depenses` · `PUT /api/depenses/<id>` · `DELETE /api/depenses/<id>`
- `POST /api/recettes` · `PUT /api/recettes/<id>` · `DELETE /api/recettes/<id>`

### Événements
- `POST /api/evenements` — créer
- `PUT /api/evenements/<id>` — modifier
- `DELETE /api/evenements/<id>` — supprimer (cascade créneaux + dispos)
- `POST /api/evenements/<id>/creneaux` — ajouter un créneau
- `DELETE /api/evenements/creneaux/<id>` — supprimer un créneau
- `POST /api/evenements/<id>/disponibilites` — enregistrer les dispos d'un participant (body: `{nom, creneau_ids:[]}`)
- `DELETE /api/evenements/disponibilites/<id>` — supprimer une dispo

### Kermesse
- `POST /api/kermesse/editions` · `PUT /api/kermesse/editions/<id>` · `DELETE /api/kermesse/editions/<id>`
- `POST /api/kermesse/<id>/stands` · `PUT /api/kermesse/stands/<id>` · `DELETE /api/kermesse/stands/<id>`
- `POST /api/kermesse/stands/<id>/inscriptions` — inscrire un bénévole (vérifie capacité)
- `DELETE /api/kermesse/inscriptions/<id>` — retirer une inscription

### Paramètres
- `POST/PUT/DELETE /api/parametres/classes/<id>`
- `GET/POST/PUT/DELETE /api/parametres/parents/<id>`
- `POST/PUT/DELETE /api/parametres/categories/<id>` — catégories dépenses/recettes

---

## Schéma SQLite (`data/app.db`)

Tables créées par `init_db()` au démarrage (`CREATE TABLE IF NOT EXISTS` + `PRAGMA journal_mode=WAL`) :

```sql
taches          -- titre, contenu, statut, important, date_echeance
depenses        -- libelle, montant, categorie (string), date_depense, notes
recettes        -- libelle, montant, categorie (string), date_recette, notes
evenements      -- titre, description, lieu, statut
evenement_creneaux       -- evenement_id, date_heure (ISO)
evenement_disponibilites -- creneau_id, nom, disponible
kermesse_editions   -- nom, date_kermesse, notes
kermesse_stands     -- edition_id, nom, description, capacite
kermesse_inscriptions   -- stand_id, nom, creneau, notes
classes         -- nom, niveau, annee_scolaire
parents         -- prenom, nom, email, telephone, classe_id, annee_scolaire, notes
categories      -- module ('depenses'|'recettes'), nom, couleur, ordre
```

### Catégories

Les catégories sont stockées dans la table `categories` (pas hardcodées). La colonne `couleur` est une clé parmi :
`bleu`, `violet`, `orange`, `vert`, `rouge`, `gris`, `rose`, `cyan`.

La palette est définie dans `db.py` :
```python
PALETTE = {
    'bleu':   {'bg': '#dbeafe', 'text': '#1e40af'},
    'violet': {'bg': '#ede9fe', 'text': '#5b21b6'},
    ...
}
```

Importée dans les routes avec `from db import get_db, PALETTE`.

**Important** : `categorie` dans `depenses` et `recettes` est stockée comme **string** (le nom de la catégorie), pas un ID. Si une catégorie est renommée via `PUT /api/parametres/categories/<id>`, les enregistrements existants sont mis à jour automatiquement.

---

## Conventions Projectix OBLIGATOIRES

### Livraison
- ZIP nommé `parentix_vX.Y.zip`
- `requirements.txt` obligatoire en v1.0 ; en relivraison (v1.1+) **uniquement si nouvelle dépendance**
- `APP_RELEASE` incrémenté à **chaque** livraison

### Templates
- Toujours `url_for()` pour les liens et assets (jamais de chemins absolus `/...`)
- `<title>` = APP_NAME uniquement
- Favicon : `<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏫</text></svg>">`
- Badge version visible en haut à droite

### JavaScript — chemins relatifs fetch()

Les pages au **niveau racine** (`/taches`, `/depenses`, etc.) utilisent :
```js
fetch('api/taches/1', ...)   // ✅ résout vers /api/taches/1
```

Les pages **imbriquées** (`/evenements/<id>`, `/kermesse/<id>`) utilisent `../` :
```js
fetch('../api/evenements/1/creneaux', ...)   // ✅ résout vers /api/evenements/1/creneaux
```

Ne jamais utiliser de chemin absolu (`fetch('/api/...')`).

**Autres règles JS :**
- Fonctions appelées depuis `onclick=""` doivent être globales (pas dans un callback `DOMContentLoaded`)
- Aucun accent dans les identifiants JS (variables, fonctions) — autorisé dans les strings uniquement

### app.run()
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
```

### Route /health (obligatoire)
```python
@app.route('/health')
def health():
    return jsonify({
        "status": "ok", "app": APP_NAME, "slug": APP_SLUG,
        "release": APP_RELEASE, "icon": APP_ICON, "color": APP_COLOR,
        "description": APP_DESCRIPTION,
        "port": int(os.environ.get('PORT', 5000)),
        "uptime_seconds": int(time.time() - start_time),
        "request_count": request_count
    })
```

---

## Design Mobile (PRIORITÉ)

**Les parents utilisent principalement leur smartphone.**

- Navigation mobile : barre fixe en bas d'écran (`.bottom-nav`) — ne jamais la supprimer ni casser
- Breakpoint mobile : `max-width: 768px`
- Sur mobile : `.nav` (header) est masquée, seule `.bottom-nav` est visible
- Padding bottom du `.container` = `80px` sur mobile pour éviter que le contenu passe sous la barre
- Grilles : `1fr` ou max `2fr` sur mobile (jamais 3+ colonnes)
- Boutons d'action dans `.page-header` : `width: 100%` sur mobile

## Design System

Tokens principaux :

```css
--primary: #1e40af;       /* Bleu FCPE */
--primary-dark: #1e3a8a;
--accent: #f59e0b;         /* Ambre */
--bg: #f8faff;
--surface: #ffffff;
--border: #dbeafe;
--text: #1e293b;
--radius: 8px;
```

Classes disponibles : `.card`, `.btn`, `.btn-primary`, `.btn-secondary`, `.badge`, `.kpi-grid`, `.kpi-card`, `.finstat-grid`, `.timeline`, `.tache-card`, `.two-col`, `.form-grid`, `.modal-overlay`, `.bottom-nav`.

### Timeline (accueil)

```html
<div class="timeline">
  <div class="timeline-item">
    <div class="timeline-dot timeline-dot-blue"></div>  <!-- blue | green | red -->
    <div class="timeline-content">…</div>
  </div>
</div>
```

---

## Checklist avant chaque livraison

- [ ] `APP_RELEASE` incrémenté
- [ ] ZIP nommé `parentix_vX.Y.zip`
- [ ] `app.py` à la racine du ZIP
- [ ] 6 variables de config présentes
- [ ] Route `/health` fonctionnelle
- [ ] CSS dans `static/css/style.css`
- [ ] `<title>` = APP_NAME uniquement
- [ ] Favicon avec APP_ICON (🏫)
- [ ] `url_for()` dans tous les templates
- [ ] Chemins relatifs corrects dans le JS (attention aux pages imbriquées `../api/...`)
- [ ] `app.run(host='0.0.0.0', port=..., debug=False)`
- [ ] Badge version visible en haut à droite
- [ ] Navigation mobile (`.bottom-nav`) intacte avec les 7 onglets
