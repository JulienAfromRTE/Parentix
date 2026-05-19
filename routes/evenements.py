from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, date
from db import get_db
import secrets

bp = Blueprint('evenements', __name__)


@bp.route('/evenements')
def evenements():
    from datetime import datetime
    db = get_db()
    rows = db.execute(
        """SELECT e.*,
           (SELECT COUNT(*) FROM evenement_creneaux ec WHERE ec.evenement_id = e.id) as nb_creneaux,
           (SELECT COUNT(DISTINCT ed.nom) FROM evenement_creneaux ec
            JOIN evenement_disponibilites ed ON ed.creneau_id = ec.id
            WHERE ec.evenement_id = e.id) as nb_participants,
           (SELECT MIN(ec.date_heure) FROM evenement_creneaux ec WHERE ec.evenement_id = e.id) as prochain_creneau
           FROM evenements e ORDER BY prochain_creneau ASC, e.created_at DESC"""
    ).fetchall()
    evenements = []
    for row in rows:
        e = dict(row)
        best = db.execute(
            """SELECT ec.date_heure, COUNT(ed.id) as nb_dispos
               FROM evenement_creneaux ec
               LEFT JOIN evenement_disponibilites ed ON ed.creneau_id = ec.id
               WHERE ec.evenement_id = ?
               GROUP BY ec.id
               ORDER BY nb_dispos DESC, ec.date_heure ASC
               LIMIT 1""", (e['id'],)
        ).fetchone()
        e['date_retenue'] = best['date_heure'] if best else None
        e['nb_dispos_max'] = best['nb_dispos'] if best else 0
        evenements.append(e)
    db.close()

    today_dt = datetime.now().date()
    today = today_dt.strftime('%Y-%m-%d')

    # Année scolaire : 1er sept → 30 juin
    y = today_dt.year if today_dt.month >= 9 else today_dt.year - 1
    sy_start = date(y, 9, 1)
    sy_end   = date(y + 1, 6, 30)
    span     = (sy_end - sy_start).days  # ~302 jours

    def to_pct(s):
        if not s:
            return None
        try:
            d = datetime.fromisoformat(s[:10]).date()
            return round(max(2.0, min(96.0, (d - sy_start).days / span * 100)), 1)
        except Exception:
            return None

    # Repères mensuels sept → juin
    _LABELS = ['sept.', 'oct.', 'nov.', 'déc.', 'janv.', 'fév.', 'mars', 'avr.', 'mai', 'juin']
    months = []
    for i, m in enumerate([9, 10, 11, 12, 1, 2, 3, 4, 5, 6]):
        yr = y if m >= 9 else y + 1
        d = date(yr, m, 1)
        months.append({'label': _LABELS[i], 'pct': round(max(1.0, (d - sy_start).days / span * 100), 1)})

    today_pct = to_pct(today)
    for e in evenements:
        e['tl_pct'] = to_pct(e.get('prochain_creneau'))

    return render_template('evenements.html', evenements=evenements, today=today,
        months=months, today_pct=today_pct,
        school_label=f"{y}–{y + 1}")


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


@bp.route('/evenements/p/<token>')
def evenement_public(token):
    db = get_db()
    evt = db.execute("SELECT * FROM evenements WHERE token=?", (token,)).fetchone()
    if not evt:
        db.close()
        return "Evenement non trouve", 404
    creneaux = db.execute(
        "SELECT * FROM evenement_creneaux WHERE evenement_id=? ORDER BY date_heure ASC", (evt['id'],)
    ).fetchall()
    creneaux_data = []
    for c in creneaux:
        nb = db.execute(
            "SELECT COUNT(*) as c FROM evenement_disponibilites WHERE creneau_id=?", (c['id'],)
        ).fetchone()['c']
        creneaux_data.append({'id': c['id'], 'date_heure': c['date_heure'], 'nb_dispos': nb})
    db.close()
    return render_template('evenement_public.html', evt=dict(evt), creneaux=creneaux_data)


@bp.route('/api/evenements', methods=['POST'])
def api_add_evenement():
    data = request.json
    token = secrets.token_hex(6)
    db = get_db()
    cur = db.execute(
        "INSERT INTO evenements (titre, description, lieu, statut, token) VALUES (?,?,?,?,?)",
        (data.get('titre', ''), data.get('description', ''),
         data.get('lieu', ''), data.get('statut', 'planification'), token)
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
