from flask import Blueprint, render_template, request, jsonify
from db import get_db

bp = Blueprint('evenements', __name__)


@bp.route('/evenements')
def evenements():
    db = get_db()
    rows = db.execute(
        """SELECT e.*,
           (SELECT COUNT(*) FROM evenement_creneaux ec WHERE ec.evenement_id = e.id) as nb_creneaux,
           (SELECT COUNT(DISTINCT ed.nom) FROM evenement_creneaux ec
            JOIN evenement_disponibilites ed ON ed.creneau_id = ec.id
            WHERE ec.evenement_id = e.id) as nb_participants,
           (SELECT MIN(ec.date_heure) FROM evenement_creneaux ec WHERE ec.evenement_id = e.id) as prochain_creneau
           FROM evenements e ORDER BY e.created_at DESC"""
    ).fetchall()
    db.close()
    return render_template('evenements.html', evenements=[dict(r) for r in rows])


@bp.route('/evenements/<int:eid>')
def evenement_detail(eid):
    db = get_db()
    evt = db.execute("SELECT * FROM evenements WHERE id=?", (eid,)).fetchone()
    if not evt:
        db.close()
        return "Evenement non trouve", 404

    creneaux = db.execute(
        "SELECT * FROM evenement_creneaux WHERE evenement_id=? ORDER BY date_heure ASC", (eid,)
    ).fetchall()

    # Pour chaque creneau, charger les disponibilites
    creneaux_data = []
    all_noms = set()
    for c in creneaux:
        dispos = db.execute(
            "SELECT * FROM evenement_disponibilites WHERE creneau_id=? ORDER BY nom ASC", (c['id'],)
        ).fetchall()
        for d in dispos:
            all_noms.add(d['nom'])
        creneaux_data.append({
            'id': c['id'],
            'date_heure': c['date_heure'],
            'dispos': {d['nom']: d for d in dispos}
        })

    all_noms = sorted(all_noms)
    db.close()
    return render_template('evenement_detail.html',
        evt=dict(evt), creneaux=creneaux_data, all_noms=all_noms)


@bp.route('/api/evenements', methods=['POST'])
def api_add_evenement():
    data = request.json
    db = get_db()
    cur = db.execute(
        "INSERT INTO evenements (titre, description, lieu, statut) VALUES (?,?,?,?)",
        (data.get('titre', ''), data.get('description', ''),
         data.get('lieu', ''), data.get('statut', 'planification'))
    )
    eid = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": eid})


@bp.route('/api/evenements/<int:eid>', methods=['PUT'])
def api_update_evenement(eid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE evenements SET titre=?, description=?, lieu=?, statut=? WHERE id=?",
        (data.get('titre', ''), data.get('description', ''),
         data.get('lieu', ''), data.get('statut', 'planification'), eid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/evenements/<int:eid>', methods=['DELETE'])
def api_delete_evenement(eid):
    db = get_db()
    cids = [r['id'] for r in db.execute(
        "SELECT id FROM evenement_creneaux WHERE evenement_id=?", (eid,)
    ).fetchall()]
    for cid in cids:
        db.execute("DELETE FROM evenement_disponibilites WHERE creneau_id=?", (cid,))
    db.execute("DELETE FROM evenement_creneaux WHERE evenement_id=?", (eid,))
    db.execute("DELETE FROM evenements WHERE id=?", (eid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/evenements/<int:eid>/creneaux', methods=['POST'])
def api_add_creneau(eid):
    data = request.json
    db = get_db()
    cur = db.execute(
        "INSERT INTO evenement_creneaux (evenement_id, date_heure) VALUES (?,?)",
        (eid, data.get('date_heure', ''))
    )
    cid = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": cid})


@bp.route('/api/evenements/creneaux/<int:cid>', methods=['DELETE'])
def api_delete_creneau(cid):
    db = get_db()
    db.execute("DELETE FROM evenement_disponibilites WHERE creneau_id=?", (cid,))
    db.execute("DELETE FROM evenement_creneaux WHERE id=?", (cid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/evenements/<int:eid>/disponibilites', methods=['POST'])
def api_set_disponibilites(eid):
    """Enregistre les disponibilites d'un participant pour un evenement.
    Body: { nom: str, creneau_ids: [int, ...] }
    Les creneaux non inclus sont retires (indisponible).
    """
    data = request.json
    nom = (data.get('nom') or '').strip()
    if not nom:
        return jsonify({"ok": False, "error": "Nom requis"}), 400

    creneau_ids_dispo = set(data.get('creneau_ids', []))

    db = get_db()
    # Recuperer tous les creneaux de l'evenement
    all_creneaux = [r['id'] for r in db.execute(
        "SELECT id FROM evenement_creneaux WHERE evenement_id=?", (eid,)
    ).fetchall()]

    for cid in all_creneaux:
        existing = db.execute(
            "SELECT id FROM evenement_disponibilites WHERE creneau_id=? AND nom=?", (cid, nom)
        ).fetchone()
        if cid in creneau_ids_dispo:
            if not existing:
                db.execute(
                    "INSERT INTO evenement_disponibilites (creneau_id, nom, disponible) VALUES (?,?,1)",
                    (cid, nom)
                )
        else:
            if existing:
                db.execute(
                    "DELETE FROM evenement_disponibilites WHERE creneau_id=? AND nom=?", (cid, nom)
                )

    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/evenements/disponibilites/<int:did>', methods=['DELETE'])
def api_delete_disponibilite(did):
    db = get_db()
    db.execute("DELETE FROM evenement_disponibilites WHERE id=?", (did,))
    db.commit()
    db.close()
    return jsonify({"ok": True})
