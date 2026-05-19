from flask import Blueprint, render_template, request, jsonify
from db import get_db

bp = Blueprint('recettes', __name__)

CATEGORIES = ['cotisation', 'subvention', 'don', 'vente', 'autre']


@bp.route('/recettes')
def recettes():
    db = get_db()
    sort = request.args.get('sort', 'date')
    cat = request.args.get('categorie', 'all')

    query = "SELECT * FROM recettes WHERE 1=1"
    params = []
    if cat != 'all':
        query += " AND categorie=?"
        params.append(cat)

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
    for c in CATEGORIES:
        totaux_cat[c] = db.execute(
            "SELECT COALESCE(SUM(montant),0) as s FROM recettes WHERE categorie=?", (c,)
        ).fetchone()['s']

    db.close()
    return render_template('recettes.html',
        recettes=rows, total=total, total_filtre=total_filtre,
        totaux_cat=totaux_cat, categories=CATEGORIES,
        sort=sort, cat_filtre=cat)


@bp.route('/api/recettes', methods=['POST'])
def api_add_recette():
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO recettes (libelle, montant, categorie, date_recette, notes) VALUES (?,?,?,?,?)",
        (data.get('libelle', ''), float(data.get('montant', 0)),
         data.get('categorie', 'cotisation'), data.get('date_recette', ''),
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
         data.get('categorie', 'cotisation'), data.get('date_recette', ''),
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
