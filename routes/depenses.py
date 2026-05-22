from flask import Blueprint, render_template, request, jsonify
from db import get_db, PALETTE
from routes.pieces_jointes import supprimer_pj_entite

bp = Blueprint('depenses', __name__)


def _get_categories(db):
    return [dict(r) for r in db.execute(
        "SELECT * FROM categories WHERE module='depenses' ORDER BY ordre, nom"
    ).fetchall()]


@bp.route('/depenses')
def depenses():
    db = get_db()
    cats = _get_categories(db)
    cat_noms = [c['nom'] for c in cats]
    sort = request.args.get('sort', 'date')
    cat_filtre = request.args.get('categorie', 'all')

    query = "SELECT * FROM depenses WHERE 1=1"
    params = []
    if cat_filtre != 'all':
        query += " AND categorie=?"
        params.append(cat_filtre)

    if sort == 'montant':
        query += " ORDER BY montant DESC"
    elif sort == 'libelle':
        query += " ORDER BY libelle ASC"
    else:
        query += " ORDER BY date_depense DESC, created_at DESC"

    rows = [dict(r) for r in db.execute(query, params).fetchall()]
    total = db.execute("SELECT COALESCE(SUM(montant),0) as s FROM depenses").fetchone()['s']
    total_filtre = sum(r['montant'] for r in rows)

    totaux_cat = {}
    for c in cats:
        totaux_cat[c['nom']] = db.execute(
            "SELECT COALESCE(SUM(montant),0) as s FROM depenses WHERE categorie=?", (c['nom'],)
        ).fetchone()['s']

    # Couleur par nom de catégorie
    couleurs = {c['nom']: PALETTE.get(c['couleur'], PALETTE['gris']) for c in cats}

    db.close()
    return render_template('depenses.html',
        depenses=rows, total=total, total_filtre=total_filtre,
        categories=cats, totaux_cat=totaux_cat, couleurs=couleurs,
        sort=sort, cat_filtre=cat_filtre)


@bp.route('/api/depenses', methods=['POST'])
def api_add_depense():
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO depenses (libelle, montant, categorie, date_depense, notes) VALUES (?,?,?,?,?)",
        (data.get('libelle', ''), float(data.get('montant', 0)),
         data.get('categorie', 'Autre'), data.get('date_depense', ''),
         data.get('notes', ''))
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/depenses/<int:did>', methods=['PUT'])
def api_update_depense(did):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE depenses SET libelle=?, montant=?, categorie=?, date_depense=?, notes=? WHERE id=?",
        (data.get('libelle', ''), float(data.get('montant', 0)),
         data.get('categorie', 'Autre'), data.get('date_depense', ''),
         data.get('notes', ''), did)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/depenses/<int:did>', methods=['DELETE'])
def api_delete_depense(did):
    db = get_db()
    supprimer_pj_entite(db, 'depense', did)
    db.execute("DELETE FROM depenses WHERE id=?", (did,))
    db.commit()
    db.close()
    return jsonify({"ok": True})
