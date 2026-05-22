import os, uuid, mimetypes
from flask import Blueprint, request, jsonify, send_file, abort
from db import get_db

bp = Blueprint('pieces_jointes', __name__)

_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
_MAX_SIZE = 10 * 1024 * 1024
_ENTITES = {'tache', 'evenement', 'depense', 'recette'}


def _chemin(entite, entite_id, nom_fichier):
    return os.path.join(_UPLOAD_DIR, entite, str(entite_id), nom_fichier)


def supprimer_pj_entite(db, entite, entite_id):
    rows = db.execute(
        "SELECT nom_fichier FROM pieces_jointes WHERE entite=? AND entite_id=?",
        (entite, entite_id)
    ).fetchall()
    for r in rows:
        path = _chemin(entite, entite_id, r['nom_fichier'])
        if os.path.isfile(path):
            os.remove(path)
    db.execute("DELETE FROM pieces_jointes WHERE entite=? AND entite_id=?", (entite, entite_id))


@bp.route('/api/pieces-jointes/<entite>/<int:entite_id>', methods=['GET'])
def api_list_pj(entite, entite_id):
    if entite not in _ENTITES:
        return jsonify({"ok": False, "error": "Entite invalide"}), 400
    db = get_db()
    rows = db.execute(
        "SELECT id, nom_original, taille, mime_type, created_at FROM pieces_jointes"
        " WHERE entite=? AND entite_id=? ORDER BY created_at DESC",
        (entite, entite_id)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/pieces-jointes/<entite>/<int:entite_id>', methods=['POST'])
def api_upload_pj(entite, entite_id):
    if entite not in _ENTITES:
        return jsonify({"ok": False, "error": "Entite invalide"}), 400
    f = request.files.get('fichier')
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "Aucun fichier"}), 400
    f.seek(0, 2)
    taille = f.tell()
    f.seek(0)
    if taille > _MAX_SIZE:
        return jsonify({"ok": False, "error": "Fichier trop volumineux (10 Mo max)"}), 400
    nom_original = f.filename
    ext = os.path.splitext(nom_original)[1].lower()
    nom_stockage = uuid.uuid4().hex + ext
    dest = os.path.join(_UPLOAD_DIR, entite, str(entite_id))
    os.makedirs(dest, exist_ok=True)
    f.save(os.path.join(dest, nom_stockage))
    mime = f.content_type or mimetypes.guess_type(nom_original)[0] or 'application/octet-stream'
    db = get_db()
    cur = db.execute(
        "INSERT INTO pieces_jointes (entite, entite_id, nom_fichier, nom_original, taille, mime_type)"
        " VALUES (?,?,?,?,?,?)",
        (entite, entite_id, nom_stockage, nom_original, taille, mime)
    )
    pj_id = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"ok": True, "id": pj_id, "nom_original": nom_original, "taille": taille})


@bp.route('/api/pieces-jointes/<int:pj_id>/download')
def api_download_pj(pj_id):
    db = get_db()
    row = db.execute("SELECT * FROM pieces_jointes WHERE id=?", (pj_id,)).fetchone()
    db.close()
    if not row:
        abort(404)
    path = _chemin(row['entite'], row['entite_id'], row['nom_fichier'])
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=row['nom_original'])


@bp.route('/api/pieces-jointes/<int:pj_id>', methods=['DELETE'])
def api_delete_pj(pj_id):
    db = get_db()
    row = db.execute("SELECT * FROM pieces_jointes WHERE id=?", (pj_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({"ok": False}), 404
    path = _chemin(row['entite'], row['entite_id'], row['nom_fichier'])
    if os.path.isfile(path):
        os.remove(path)
    db.execute("DELETE FROM pieces_jointes WHERE id=?", (pj_id,))
    db.commit()
    db.close()
    return jsonify({"ok": True})
