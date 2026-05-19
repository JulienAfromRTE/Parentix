from flask import Blueprint, render_template, request, jsonify
from db import get_db, PALETTE

bp = Blueprint('recettes', __name__)


def _get_categories(db):
    return [dict(r) for r in db.execute(
        "SELECT * FROM categories WHERE module='recettes' ORDER BY ordre, nom"
    ).fetchall()]


@bp.route('/recettes')
def recettes():
    db = get_db()
    cats = _get_categories(db)
    sort = request.args.get('sort', 'date')
    cat_filtre = request.args.get('categorie', 'all')

    query = "SELECT * FROM recettes WHERE 1=1"
    params = []
    if cat_filtre != 'all':
        query += " AND categorie=?"
        params.append(cat_filtre)

    if sort == 'montant':
        query += " ORDER BY montant DESC"
    elif sort == 'libelle':
        query += " ORDER BY libelle ASC"
    else:
        query += " ORDER BY date_recette DESC, created_at DESC"

    rows = [dict(r) for r in db.execute(query, params).fetchall()]
    total = db.execute("SELECT COALESCE(SUM(montant),0) as s FROM recettes").fetchone()['s']
    total_filtre = sum(r['montant'] for r in rows)

    totaux_cat = {}
    for c in cats:
        totaux_cat[c['nom']] = db.execute(
            "SELECT COALESCE(SUM(montant),0) as s FROM recettes WHERE categorie=?", (c['nom'],)
        ).fetchone()['s']

    couleurs = {c['nom']: PALETTE.get(c['couleur'], PALETTE['gris']) for c in cats}

    db.close()
    return render_template('recettes.html',
        recettes=rows, total=total, total_filtre=total_filtre,
        categories=cats, totaux_cat=totaux_cat, couleurs=couleurs,
        sort=sort, cat_filtre=cat_filtre)


@bp.route('/api/recettes', methods=['POST'])
def api_add_recette():
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO recettes (libelle, montant, categorie, date_recette, notes) VALUES (?,?,?,?,?)",
        (data.get('libelle', ''), float(data.get('montant', 0)),
         data.get('categorie', 'Cotisation'), data.get('date_recette', ''),
         data.get('notes', ''))
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/recettes/<int:rid>', methods=['PUT'])
def api_update_recette(rid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE recettes SET libelle=?, montant=?, categorie=?, date_recette=?, notes=? WHERE id=?",
        (data.get('libelle', ''), float(data.get('montant', 0)),
         data.get('categorie', 'Cotisation'), data.get('date_recette', ''),
         data.get('notes', ''), rid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/recettes/<int:rid>', methods=['DELETE'])
def api_delete_recette(rid):
    db = get_db()
    db.execute("DELETE FROM recettes WHERE id=?", (rid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})
