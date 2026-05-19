from flask import Blueprint, render_template, request, jsonify
from db import get_db, PALETTE

bp = Blueprint('parametres', __name__)


@bp.route('/parametres')
def parametres():
    db = get_db()
    annee = request.args.get('annee', '2025-2026')
    cats_depenses = [dict(r) for r in db.execute(
        "SELECT * FROM categories WHERE module='depenses' ORDER BY ordre, nom"
    ).fetchall()]
    cats_recettes = [dict(r) for r in db.execute(
        "SELECT * FROM categories WHERE module='recettes' ORDER BY ordre, nom"
    ).fetchall()]

    classes = db.execute(
        "SELECT c.*, (SELECT COUNT(*) FROM parents p WHERE p.classe_id = c.id AND p.annee_scolaire=?) as nb_parents "
        "FROM classes c WHERE c.annee_scolaire=? ORDER BY c.nom ASC",
        (annee, annee)
    ).fetchall()

    parents = db.execute(
        "SELECT p.*, c.nom as classe_nom FROM parents p "
        "LEFT JOIN classes c ON p.classe_id = c.id "
        "WHERE p.annee_scolaire=? ORDER BY p.nom ASC, p.prenom ASC",
        (annee,)
    ).fetchall()

    annees = [r['annee_scolaire'] for r in db.execute(
        "SELECT DISTINCT annee_scolaire FROM parents ORDER BY annee_scolaire DESC"
    ).fetchall()]
    if annee not in annees:
        annees.append(annee)

    db.close()
    return render_template('parametres.html',
        classes=[dict(c) for c in classes],
        parents=[dict(p) for p in parents],
        annee=annee, annees=sorted(set(annees), reverse=True),
        cats_depenses=cats_depenses, cats_recettes=cats_recettes,
        palette=PALETTE)


@bp.route('/api/parametres/categories', methods=['POST'])
def api_add_categorie():
    data = request.json
    db = get_db()
    cur = db.execute(
        "INSERT INTO categories (module, nom, couleur, ordre) VALUES (?,?,?,?)",
        (data.get('module', 'depenses'), data.get('nom', ''),
         data.get('couleur', 'gris'),
         int(data.get('ordre', 99)))
    )
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": cur.lastrowid})


@bp.route('/api/parametres/categories/<int:cid>', methods=['PUT'])
def api_update_categorie(cid):
    data = request.json
    db = get_db()
    old = db.execute("SELECT nom FROM categories WHERE id=?", (cid,)).fetchone()
    new_nom = data.get('nom', '')
    if old and old['nom'] != new_nom:
        module = db.execute("SELECT module FROM categories WHERE id=?", (cid,)).fetchone()['module']
        table = 'depenses' if module == 'depenses' else 'recettes'
        db.execute(f"UPDATE {table} SET categorie=? WHERE categorie=?", (new_nom, old['nom']))
    db.execute(
        "UPDATE categories SET nom=?, couleur=?, ordre=? WHERE id=?",
        (new_nom, data.get('couleur', 'gris'), int(data.get('ordre', 99)), cid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/parametres/categories/<int:cid>', methods=['DELETE'])
def api_delete_categorie(cid):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id=?", (cid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/parametres/classes', methods=['POST'])
def api_add_classe():
    data = request.json
    db = get_db()
    cur = db.execute(
        "INSERT INTO classes (nom, niveau, annee_scolaire) VALUES (?,?,?)",
        (data.get('nom', ''), data.get('niveau', ''),
         data.get('annee_scolaire', '2025-2026'))
    )
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": cur.lastrowid})


@bp.route('/api/parametres/classes/<int:cid>', methods=['PUT'])
def api_update_classe(cid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE classes SET nom=?, niveau=? WHERE id=?",
        (data.get('nom', ''), data.get('niveau', ''), cid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/parametres/classes/<int:cid>', methods=['DELETE'])
def api_delete_classe(cid):
    db = get_db()
    db.execute("UPDATE parents SET classe_id=NULL WHERE classe_id=?", (cid,))
    db.execute("DELETE FROM classes WHERE id=?", (cid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/parametres/parents', methods=['GET'])
def api_list_parents():
    db = get_db()
    parents = [dict(r) for r in db.execute(
        "SELECT id, prenom, nom FROM parents ORDER BY nom ASC, prenom ASC"
    ).fetchall()]
    db.close()
    return jsonify(parents)


@bp.route('/api/parametres/parents', methods=['POST'])
def api_add_parent():
    data = request.json
    db = get_db()
    cur = db.execute(
        "INSERT INTO parents (prenom, nom, email, telephone, classe_id, annee_scolaire, notes) VALUES (?,?,?,?,?,?,?)",
        (data.get('prenom', ''), data.get('nom', ''),
         data.get('email', ''), data.get('telephone', ''),
         data.get('classe_id') or None,
         data.get('annee_scolaire', '2025-2026'),
         data.get('notes', ''))
    )
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": cur.lastrowid})


@bp.route('/api/parametres/parents/<int:pid>', methods=['PUT'])
def api_update_parent(pid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE parents SET prenom=?, nom=?, email=?, telephone=?, classe_id=?, notes=? WHERE id=?",
        (data.get('prenom', ''), data.get('nom', ''),
         data.get('email', ''), data.get('telephone', ''),
         data.get('classe_id') or None,
         data.get('notes', ''), pid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/parametres/parents/<int:pid>', methods=['DELETE'])
def api_delete_parent(pid):
    db = get_db()
    db.execute("DELETE FROM parents WHERE id=?", (pid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})
