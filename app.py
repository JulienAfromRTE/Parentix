# -*- coding: utf-8 -*-
APP_NAME    = "Parentix"
APP_SLUG    = "parentix"
APP_RELEASE = "v1.0"
APP_DESCRIPTION = "Pilotage de l'association FCPE : taches, depenses, recettes, evenements, kermesse"
APP_ICON    = "🏫"
APP_COLOR   = "#1e40af"
APP_CATEGORY = ""

import os, time, logging
from flask import Flask, render_template, jsonify, session, redirect, url_for, request, make_response, send_from_directory
from functools import wraps
from db import init_db, get_db

USERS = {"admin": "parentix"}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

from routes.taches import bp as taches_bp
from routes.depenses import bp as depenses_bp
from routes.recettes import bp as recettes_bp
from routes.evenements import bp as evenements_bp
from routes.kermesse import bp as kermesse_bp
from routes.parametres import bp as parametres_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(APP_NAME)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-parentix')

app.register_blueprint(taches_bp)
app.register_blueprint(depenses_bp)
app.register_blueprint(recettes_bp)
app.register_blueprint(evenements_bp)
app.register_blueprint(kermesse_bp)
app.register_blueprint(parametres_bp)

request_count = 0
start_time = time.time()


@app.context_processor
def inject_app_vars():
    return dict(APP_NAME=APP_NAME, APP_ICON=APP_ICON, APP_RELEASE=APP_RELEASE, APP_COLOR=APP_COLOR)


@app.before_request
def count_requests():
    global request_count
    request_count += 1


@app.before_request
def require_login():
    public = {'login', 'logout', 'health', 'static', 'service_worker'}
    if request.endpoint and request.endpoint.split('.')[0] in public:
        return
    if not session.get('logged_in'):
        return redirect(url_for('login', next=request.path))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if USERS.get(username) == password:
            session['logged_in'] = True
            session['username'] = username
            next_url = request.form.get('next') or ''
            return render_template('login_redirect.html', next_url=next_url)
        error = "Identifiant ou mot de passe incorrect."
    return render_template('login.html', error=error, next=request.args.get('next', ''))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/sw.js')
def service_worker():
    resp = make_response(send_from_directory('static', 'sw.js'))
    resp.headers['Content-Type'] = 'application/javascript'
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


@app.route('/health')
def health():
    return jsonify({
        "status": "ok", "app": APP_NAME, "slug": APP_SLUG,
        "release": APP_RELEASE, "icon": APP_ICON, "color": APP_COLOR,
        "description": APP_DESCRIPTION,
        "port": int(os.environ.get('PORT', 5000)),
        "uptime_seconds": int(time.time() - start_time),
        "request_count": request_count
    })


@app.route('/')
def index():
    db = get_db()
    from datetime import date
    today = date.today().isoformat()

    nb_taches = db.execute("SELECT COUNT(*) as c FROM taches WHERE statut != 'clos'").fetchone()['c']
    total_depenses = db.execute("SELECT COALESCE(SUM(montant),0) as s FROM depenses").fetchone()['s']
    total_recettes = db.execute("SELECT COALESCE(SUM(montant),0) as s FROM recettes").fetchone()['s']
    nb_parents = db.execute("SELECT COUNT(*) as c FROM parents").fetchone()['c']
    nb_evenements = db.execute("SELECT COUNT(*) as c FROM evenements WHERE statut != 'annule'").fetchone()['c']

    taches_a_venir = db.execute(
        "SELECT * FROM taches WHERE statut != 'clos' ORDER BY important DESC, date_echeance ASC NULLS LAST, created_at DESC LIMIT 7"
    ).fetchall()

    prochains_evenements = db.execute(
        """SELECT e.*,
           (SELECT COUNT(DISTINCT ed.nom) FROM evenement_creneaux ec
            JOIN evenement_disponibilites ed ON ed.creneau_id = ec.id
            WHERE ec.evenement_id = e.id) as nb_reponses,
           (SELECT MIN(ec.date_heure) FROM evenement_creneaux ec WHERE ec.evenement_id = e.id) as prochain_creneau
           FROM evenements e
           WHERE e.statut != 'annule'
           ORDER BY prochain_creneau ASC NULLS LAST, e.created_at DESC
           LIMIT 5"""
    ).fetchall()

    depenses_recentes = db.execute(
        "SELECT * FROM depenses ORDER BY date_depense DESC, created_at DESC LIMIT 5"
    ).fetchall()
    recettes_recentes = db.execute(
        "SELECT * FROM recettes ORDER BY date_recette DESC, created_at DESC LIMIT 5"
    ).fetchall()

    solde = total_recettes - total_depenses
    db.close()

    return render_template('index.html',
        nb_taches=nb_taches, total_depenses=total_depenses,
        total_recettes=total_recettes, nb_parents=nb_parents,
        nb_evenements=nb_evenements,
        taches_a_venir=taches_a_venir, prochains_evenements=prochains_evenements,
        depenses_recentes=depenses_recentes, recettes_recentes=recettes_recentes,
        solde=solde, today=today)


init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
