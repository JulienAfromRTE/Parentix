# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
from db import get_db
import secrets

bp = Blueprint('votes', __name__)


@bp.route('/votes')
def votes():
    db = get_db()
    rows = db.execute("""
        SELECT v.*,
        (SELECT COUNT(*) FROM vote_options o WHERE o.vote_id = v.id) as nb_options,
        (SELECT COUNT(DISTINCT nom) FROM vote_reponses r WHERE r.vote_id = v.id) as nb_repondants
        FROM votes v ORDER BY v.created_at DESC
    """).fetchall()
    db.close()
    return render_template('votes.html', votes=[dict(r) for r in rows])


@bp.route('/votes/<int:vid>')
def vote_detail(vid):
    db = get_db()
    vote = db.execute("SELECT * FROM votes WHERE id=?", (vid,)).fetchone()
    if not vote:
        db.close()
        return "Vote non trouve", 404

    options_raw = db.execute(
        "SELECT * FROM vote_options WHERE vote_id=? ORDER BY ordre ASC", (vid,)
    ).fetchall()

    repondants = db.execute(
        "SELECT DISTINCT nom FROM vote_reponses WHERE vote_id=? ORDER BY nom ASC", (vid,)
    ).fetchall()
    total_repondants = len(repondants)

    options = []
    for opt in options_raw:
        nb = db.execute(
            "SELECT COUNT(DISTINCT nom) as c FROM vote_reponses WHERE vote_id=? AND option_id=?",
            (vid, opt['id'])
        ).fetchone()['c']
        pct = round(nb * 100 / total_repondants) if total_repondants > 0 else 0
        options.append({'id': opt['id'], 'texte': opt['texte'], 'ordre': opt['ordre'],
                        'nb_votes': nb, 'pct': pct})

    db.close()
    return render_template('vote_detail.html',
        vote=dict(vote),
        options=options,
        repondants=[r['nom'] for r in repondants],
        total_repondants=total_repondants)


@bp.route('/votes/p/<token>')
def vote_public(token):
    db = get_db()
    vote = db.execute("SELECT * FROM votes WHERE token=?", (token,)).fetchone()
    if not vote:
        db.close()
        return "Sondage non trouve", 404

    options = db.execute(
        "SELECT * FROM vote_options WHERE vote_id=? ORDER BY ordre ASC", (vote['id'],)
    ).fetchall()
    db.close()
    return render_template('vote_public.html',
        vote=dict(vote),
        options=[dict(o) for o in options])


# --- API ---

@bp.route('/api/votes', methods=['POST'])
def api_add_vote():
    data = request.json
    titre = (data.get('titre') or '').strip()
    if not titre:
        return jsonify({"ok": False, "error": "Titre requis"}), 400

    token = secrets.token_hex(6)
    db = get_db()
    cur = db.execute(
        "INSERT INTO votes (titre, description, type, statut, token) VALUES (?,?,?,?,?)",
        (titre, data.get('description', ''), data.get('type', 'unique'), 'ouvert', token)
    )
    vid = cur.lastrowid
    for i, texte in enumerate(data.get('options', []), 1):
        if texte.strip():
            db.execute(
                "INSERT INTO vote_options (vote_id, texte, ordre) VALUES (?,?,?)",
                (vid, texte.strip(), i)
            )
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": vid})


@bp.route('/api/votes/<int:vid>', methods=['PUT'])
def api_update_vote(vid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE votes SET titre=?, description=?, type=?, statut=? WHERE id=?",
        (data.get('titre', ''), data.get('description', ''),
         data.get('type', 'unique'), data.get('statut', 'ouvert'), vid)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/votes/<int:vid>', methods=['DELETE'])
def api_delete_vote(vid):
    db = get_db()
    db.execute("DELETE FROM vote_reponses WHERE vote_id=?", (vid,))
    db.execute("DELETE FROM vote_options WHERE vote_id=?", (vid,))
    db.execute("DELETE FROM votes WHERE id=?", (vid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/votes/<int:vid>/statut', methods=['PUT'])
def api_toggle_statut(vid):
    db = get_db()
    vote = db.execute("SELECT statut FROM votes WHERE id=?", (vid,)).fetchone()
    if not vote:
        db.close()
        return jsonify({"ok": False}), 404
    new_statut = 'clos' if vote['statut'] == 'ouvert' else 'ouvert'
    db.execute("UPDATE votes SET statut=? WHERE id=?", (new_statut, vid))
    db.commit()
    db.close()
    return jsonify({"ok": True, "statut": new_statut})


@bp.route('/api/votes/<int:vid>/options', methods=['POST'])
def api_add_option(vid):
    data = request.json
    texte = (data.get('texte') or '').strip()
    if not texte:
        return jsonify({"ok": False, "error": "Texte requis"}), 400
    db = get_db()
    max_ordre = db.execute(
        "SELECT COALESCE(MAX(ordre),0) as m FROM vote_options WHERE vote_id=?", (vid,)
    ).fetchone()['m']
    cur = db.execute(
        "INSERT INTO vote_options (vote_id, texte, ordre) VALUES (?,?,?)",
        (vid, texte, max_ordre + 1)
    )
    oid = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": oid})


@bp.route('/api/votes/options/<int:oid>', methods=['DELETE'])
def api_delete_option(oid):
    db = get_db()
    db.execute("DELETE FROM vote_reponses WHERE option_id=?", (oid,))
    db.execute("DELETE FROM vote_options WHERE id=?", (oid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/votes/<int:vid>/repondre', methods=['POST'])
def api_repondre(vid):
    """Body: {nom, option_ids: [int, ...]}"""
    data = request.json
    nom = (data.get('nom') or '').strip()
    if not nom:
        return jsonify({"ok": False, "error": "Nom requis"}), 400

    db = get_db()
    vote = db.execute("SELECT * FROM votes WHERE id=?", (vid,)).fetchone()
    if not vote:
        db.close()
        return jsonify({"ok": False, "error": "Vote introuvable"}), 404
    if vote['statut'] == 'clos':
        db.close()
        return jsonify({"ok": False, "error": "Ce sondage est clos"}), 400

    valid_opts = {r['id'] for r in db.execute(
        "SELECT id FROM vote_options WHERE vote_id=?", (vid,)
    ).fetchall()}
    option_ids = [oid for oid in (data.get('option_ids') or []) if oid in valid_opts]

    if vote['type'] == 'unique' and len(option_ids) > 1:
        option_ids = [option_ids[0]]

    db.execute("DELETE FROM vote_reponses WHERE vote_id=? AND nom=?", (vid, nom))
    for oid in option_ids:
        db.execute(
            "INSERT INTO vote_reponses (vote_id, option_id, nom) VALUES (?,?,?)",
            (vid, oid, nom)
        )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@bp.route('/api/votes/<int:vid>/repondants/<path:nom>', methods=['DELETE'])
def api_delete_repondant(vid, nom):
    db = get_db()
    db.execute("DELETE FROM vote_reponses WHERE vote_id=? AND nom=?", (vid, nom))
    db.commit()
    db.close()
    return jsonify({"ok": True})
