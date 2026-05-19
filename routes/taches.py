from flask import Blueprint, render_template, request, jsonify
from db import get_db

bp = Blueprint('taches', __name__)


@bp.route('/taches')
def taches():
    db = get_db()
    statut_filtre = request.args.get('statut', '')
    important_filtre = request.args.get('important', '')
    tri = request.args.get('tri', 'created_at')
    recherche = request.args.get('q', '').strip()

    query = "SELECT * FROM taches WHERE 1=1"
    params = []
    if statut_filtre:
        query += " AND statut=?"
        params.append(statut_filtre)
    if important_filtre == '1':
        query += " AND important=1"
    if recherche:
        query += " AND (titre LIKE ? OR contenu LIKE ?)"
        params.extend([f'%{recherche}%', f'%{recherche}%'])

    if tri == 'date_echeance':
        query += " ORDER BY important DESC, date_echeance ASC NULLS LAST, created_at DESC"
    else:
        query += " ORDER BY important DESC, created_at DESC"

    rows = [dict(r) for r in db.execute(query, params).fetchall()]

    nb_nouveau = db.execute("SELECT COUNT(*) as c FROM taches WHERE statut='nouveau'").fetchone()['c']
    nb_en_cours = db.execute("SELECT COUNT(*) as c FROM taches WHERE statut='en_cours'").fetchone()['c']
    nb_clos = db.execute("SELECT COUNT(*) as c FROM taches WHERE statut='clos'").fetchone()['c']
    nb_important = db.execute("SELECT COUNT(*) as c FROM taches WHERE important=1 AND statut!='clos'").fetchone()['c']
    db.close()

    return render_template('taches.html',
        taches=rows,
        statut_filtre=statut_filtre, important_filtre=important_filtre,
        tri=tri, recherche=recherche,
        nb_nouveau=nb_nouveau, nb_en_cours=nb_en_cours,
        nb_clos=nb_clos, nb_important=nb_important,
        nb_total=nb_nouveau + nb_en_cours + nb_clos)


@bp.route('/api/taches', methods=['POST'])
def api_add_tache():
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO taches (titre, contenu, statut, important, date_echeance) VALUES (?,?,?,?,?)",
        (data.get('titre', '').strip(), data.get('contenu', ''),
         data.get('statut', 'nouveau'),
         1 if data.get('important') else 0,
         data.get('date_echeance') or None)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/taches/<int:tid>', methods=['PUT'])
def api_update_tache(tid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE taches SET titre=?, contenu=?, statut=?, important=?, date_echeance=? WHERE id=?",
        (data.get('titre', '').strip(), data.get('contenu', ''),
         data.get('statut', 'nouveau'),
         1 if data.get('important') else 0,
         data.get('date_echeance') or None, tid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/taches/<int:tid>', methods=['DELETE'])
def api_delete_tache(tid):
    db = get_db()
    db.execute("DELETE FROM taches WHERE id=?", (tid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/taches/<int:tid>/statut', methods=['PUT'])
def api_update_statut(tid):
    statut = request.json.get('statut', 'nouveau')
    db = get_db()
    db.execute("UPDATE taches SET statut=? WHERE id=?", (statut, tid))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/taches/<int:tid>/important', methods=['PUT'])
def api_toggle_important(tid):
    db = get_db()
    row = db.execute("SELECT important FROM taches WHERE id=?", (tid,)).fetchone()
    if row:
        new_val = 0 if row['important'] else 1
        db.execute("UPDATE taches SET important=? WHERE id=?", (new_val, tid))
        db.commit()
        db.close()
        return jsonify({"ok": True, "important": new_val})
    db.close()
    return jsonify({"ok": False}), 404
