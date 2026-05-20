from flask import Blueprint, request, jsonify
from db import get_db

bp = Blueprint('commentaires', __name__)

_ENTITES = {'tache', 'evenement', 'kermesse_stand', 'vote'}


@bp.route('/api/commentaires/<entite>/<int:eid>', methods=['GET'])
def list_commentaires(entite, eid):
    if entite not in _ENTITES:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        "SELECT id, entite, entite_id, auteur, contenu, created_at FROM commentaires "
        "WHERE entite=? AND entite_id=? ORDER BY created_at ASC",
        (entite, eid)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/commentaires/<entite>/<int:eid>', methods=['POST'])
def add_commentaire(entite, eid):
    if entite not in _ENTITES:
        return jsonify({'ok': False, 'error': 'Entite invalide'}), 400
    data = request.json or {}
    auteur = (data.get('auteur') or '').strip()
    contenu = (data.get('contenu') or '').strip()
    if not auteur:
        return jsonify({'ok': False, 'error': 'Auteur requis'}), 400
    if not contenu or contenu == '<p><br></p>':
        return jsonify({'ok': False, 'error': 'Commentaire vide'}), 400
    db = get_db()
    db.execute(
        "INSERT INTO commentaires (entite, entite_id, auteur, contenu) VALUES (?,?,?,?)",
        (entite, eid, auteur, contenu)
    )
    db.commit()
    db.close()
    return jsonify({'ok': True})


@bp.route('/api/commentaires/<int:cid>', methods=['DELETE'])
def delete_commentaire(cid):
    db = get_db()
    db.execute("DELETE FROM commentaires WHERE id=?", (cid,))
    db.commit()
    db.close()
    return jsonify({'ok': True})
