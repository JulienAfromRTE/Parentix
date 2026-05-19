from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from db import get_db
from datetime import date

bp = Blueprint('kermesse', __name__)


@bp.route('/kermesse')
def kermesse():
    db = get_db()
    today = date.today().isoformat()
    # Kermesse à venir la plus proche, sinon la plus récente
    prochaine = db.execute(
        """SELECT id FROM kermesse_editions
           WHERE date_kermesse >= ?
           ORDER BY date_kermesse ASC LIMIT 1""",
        (today,)
    ).fetchone()
    if not prochaine:
        prochaine = db.execute(
            "SELECT id FROM kermesse_editions ORDER BY date_kermesse DESC, created_at DESC LIMIT 1"
        ).fetchone()
    if prochaine:
        db.close()
        return redirect(url_for('kermesse.kermesse_detail', eid=prochaine['id']))
    editions = db.execute(
        """SELECT e.*,
           (SELECT COUNT(*) FROM kermesse_stands s WHERE s.edition_id = e.id) as nb_stands,
           (SELECT COUNT(*) FROM kermesse_inscriptions i
            JOIN kermesse_stands s ON i.stand_id = s.id
            WHERE s.edition_id = e.id) as nb_inscrits
           FROM kermesse_editions e ORDER BY e.date_kermesse DESC, e.created_at DESC"""
    ).fetchall()
    db.close()
    return render_template('kermesse.html', editions=[dict(e) for e in editions])


@bp.route('/kermesse/<int:eid>')
def kermesse_detail(eid):
    db = get_db()
    edition = db.execute("SELECT * FROM kermesse_editions WHERE id=?", (eid,)).fetchone()
    if not edition:
        db.close()
        return "Edition non trouvee", 404

    stands = db.execute(
        "SELECT * FROM kermesse_stands WHERE edition_id=? ORDER BY nom ASC", (eid,)
    ).fetchall()

    stands_data = []
    for s in stands:
        inscrits = db.execute(
            "SELECT * FROM kermesse_inscriptions WHERE stand_id=? ORDER BY created_at ASC", (s['id'],)
        ).fetchall()
        stands_data.append({
            'id': s['id'],
            'nom': s['nom'],
            'description': s['description'],
            'capacite': s['capacite'],
            'inscrits': [dict(i) for i in inscrits],
            'nb_inscrits': len(inscrits),
            'places_restantes': max(0, s['capacite'] - len(inscrits))
        })

    db.close()
    return render_template('kermesse_detail.html',
        edition=dict(edition), stands=stands_data)


@bp.route('/api/kermesse/editions', methods=['POST'])
def api_add_edition():
    data = request.json
    db = get_db()
    cur = db.execute(
        "INSERT INTO kermesse_editions (nom, date_kermesse, notes) VALUES (?,?,?)",
        (data.get('nom', ''), data.get('date_kermesse', ''), data.get('notes', ''))
    )
    eid = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": eid})


@bp.route('/api/kermesse/editions/<int:eid>', methods=['PUT'])
def api_update_edition(eid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE kermesse_editions SET nom=?, date_kermesse=?, notes=? WHERE id=?",
        (data.get('nom', ''), data.get('date_kermesse', ''), data.get('notes', ''), eid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/kermesse/editions/<int:eid>', methods=['DELETE'])
def api_delete_edition(eid):
    db = get_db()
    sids = [r['id'] for r in db.execute(
        "SELECT id FROM kermesse_stands WHERE edition_id=?", (eid,)
    ).fetchall()]
    for sid in sids:
        db.execute("DELETE FROM kermesse_inscriptions WHERE stand_id=?", (sid,))
    db.execute("DELETE FROM kermesse_stands WHERE edition_id=?", (eid,))
    db.execute("DELETE FROM kermesse_editions WHERE id=?", (eid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/kermesse/<int:eid>/stands', methods=['POST'])
def api_add_stand(eid):
    data = request.json
    db = get_db()
    cur = db.execute(
        "INSERT INTO kermesse_stands (edition_id, nom, description, capacite) VALUES (?,?,?,?)",
        (eid, data.get('nom', ''), data.get('description', ''),
         int(data.get('capacite', 2)))
    )
    sid = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": sid})


@bp.route('/api/kermesse/stands/<int:sid>', methods=['PUT'])
def api_update_stand(sid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE kermesse_stands SET nom=?, description=?, capacite=? WHERE id=?",
        (data.get('nom', ''), data.get('description', ''),
         int(data.get('capacite', 2)), sid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/kermesse/stands/<int:sid>', methods=['DELETE'])
def api_delete_stand(sid):
    db = get_db()
    db.execute("DELETE FROM kermesse_inscriptions WHERE stand_id=?", (sid,))
    db.execute("DELETE FROM kermesse_stands WHERE id=?", (sid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/kermesse/stands/<int:sid>/inscriptions', methods=['POST'])
def api_add_inscription(sid):
    data = request.json
    nom = (data.get('nom') or '').strip()
    if not nom:
        return jsonify({"ok": False, "error": "Nom requis"}), 400
    db = get_db()
    stand = db.execute("SELECT * FROM kermesse_stands WHERE id=?", (sid,)).fetchone()
    if not stand:
        db.close()
        return jsonify({"ok": False, "error": "Stand introuvable"}), 404
    nb = db.execute("SELECT COUNT(*) as c FROM kermesse_inscriptions WHERE stand_id=?", (sid,)).fetchone()['c']
    if nb >= stand['capacite']:
        db.close()
        return jsonify({"ok": False, "error": "Stand complet"}), 400
    cur = db.execute(
        "INSERT INTO kermesse_inscriptions (stand_id, nom, creneau, notes) VALUES (?,?,?,?)",
        (sid, nom, data.get('creneau', 'journee'), data.get('notes', ''))
    )
    iid = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": iid})


@bp.route('/api/kermesse/inscriptions/<int:iid>', methods=['DELETE'])
def api_delete_inscription(iid):
    db = get_db()
    db.execute("DELETE FROM kermesse_inscriptions WHERE id=?", (iid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})
