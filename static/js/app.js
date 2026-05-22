// ─── MODAL GLOBAL ───────────────────────────────────────────────────────────
function openModal(titre, contenu) {
  document.getElementById('modal-title').textContent = titre;
  document.getElementById('modal-body').innerHTML = contenu;
  document.getElementById('modal-overlay').style.display = 'flex';
}

function closeModal() {
  document.getElementById('modal-overlay').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
  var overlay = document.getElementById('modal-overlay');
  if (overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) closeModal();
    });
  }
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') { closeModal(); closeBurgerMenu(); }
  });
});

// ─── BURGER MENU ─────────────────────────────────────────────────────────────
function toggleBurgerMenu() {
  var menu = document.getElementById('burger-menu');
  if (menu) menu.classList.toggle('open');
}

function closeBurgerMenu() {
  var menu = document.getElementById('burger-menu');
  if (menu) menu.classList.remove('open');
}

function closeBurgerOnBackdrop(e) {
  if (e.target === document.getElementById('burger-menu')) closeBurgerMenu();
}

// ─── COPIER LIEN (avec fallback HTTP) ────────────────────────────────────────
function copierLien(url) {
  function afficherToast() {
    var t = document.getElementById('toast-lien');
    if (!t) {
      t = document.createElement('div');
      t.id = 'toast-lien';
      t.style.cssText = 'position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:#1e293b;color:#fff;padding:10px 20px;border-radius:8px;font-size:0.85rem;z-index:9999;';
      document.body.appendChild(t);
    }
    t.textContent = '✅ Lien copié !';
    t.style.display = 'block';
    setTimeout(function(){ t.style.display = 'none'; }, 2000);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(afficherToast).catch(function(){ _copierFallback(url, afficherToast); });
  } else {
    _copierFallback(url, afficherToast);
  }
}

// ─── UTILITAIRE ──────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── COMMENTAIRES ────────────────────────────────────────────────────────────
var _cmQuill = null;
var _inlineCmQuill = null;

function ouvrirCommentairesBtn(btn) {
  ouvrirCommentaires(
    btn.getAttribute('data-entite'),
    parseInt(btn.getAttribute('data-eid')),
    btn.getAttribute('data-titre'),
    btn.getAttribute('data-prefix')
  );
}

function ouvrirCommentaires(entite, eid, titre, urlPrefix) {
  openModal('💬 ' + titre,
    '<div id="cm-list" style="max-height:260px;overflow-y:auto;margin-bottom:4px;"></div>' +
    '<div style="border-top:1px solid var(--border);padding-top:14px;margin-top:4px;">' +
    '<label style="font-weight:600;font-size:0.82rem;display:block;margin-bottom:4px;">Votre nom</label>' +
    '<input type="text" id="cm-auteur" list="cm-parents-dl" placeholder="Choisir parmi les parents ou saisie libre" autocomplete="off" style="margin-bottom:10px;">' +
    '<datalist id="cm-parents-dl"></datalist>' +
    '<label style="font-weight:600;font-size:0.82rem;display:block;margin-bottom:4px;">Commentaire</label>' +
    '<div id="cm-editor"></div>' +
    '</div>' +
    '<div class="form-actions" style="margin-top:10px;">' +
    '<button type="button" class="btn btn-secondary" onclick="closeModal()">Fermer</button>' +
    '<button type="button" class="btn btn-primary" onclick="_soumettreCommentaireMod(\'' + entite + '\',' + eid + ',\'' + urlPrefix + '\')">Publier</button>' +
    '</div>'
  );
  _cmQuill = new Quill('#cm-editor', {
    theme: 'snow',
    placeholder: 'Votre commentaire…',
    modules: { toolbar: [['bold','italic','underline'],[{list:'bullet'}],['clean']] }
  });
  _chargerCommentaires(entite, eid, urlPrefix, 'cm-list', true);
  fetch(urlPrefix + 'api/parametres/parents')
    .then(function(r){ return r.json(); })
    .then(function(parents){
      var dl = document.getElementById('cm-parents-dl');
      if (!dl) return;
      parents.forEach(function(p) {
        var opt = document.createElement('option');
        opt.value = p.prenom + ' ' + p.nom;
        dl.appendChild(opt);
      });
    }).catch(function(){});
}

function initCommentairesInline(entite, eid, urlPrefix) {
  _chargerCommentaires(entite, eid, urlPrefix, 'inline-cm-list', false);
  if (document.getElementById('inline-cm-editor')) {
    _inlineCmQuill = new Quill('#inline-cm-editor', {
      theme: 'snow',
      placeholder: 'Votre commentaire…',
      modules: { toolbar: [['bold','italic','underline'],[{list:'bullet'}],['clean']] }
    });
  }
  fetch(urlPrefix + 'api/parametres/parents')
    .then(function(r){ return r.json(); })
    .then(function(parents){
      var dl = document.getElementById('inline-cm-parents-dl');
      if (!dl) return;
      parents.forEach(function(p) {
        var opt = document.createElement('option');
        opt.value = p.prenom + ' ' + p.nom;
        dl.appendChild(opt);
      });
    }).catch(function(){});
}

function _chargerCommentaires(entite, eid, urlPrefix, containerId, inModal) {
  var container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;padding:4px 0;">Chargement…</p>';
  fetch(urlPrefix + 'api/commentaires/' + entite + '/' + eid)
    .then(function(r){ return r.json(); })
    .then(function(comments){ _renderCommentaires(comments, container, entite, eid, urlPrefix, inModal); })
    .catch(function(){ container.innerHTML = '<p style="color:#dc2626;font-size:0.82rem;">Erreur de chargement.</p>'; });
}

function _renderCommentaires(comments, container, entite, eid, urlPrefix, inModal) {
  if (!comments.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;font-style:italic;margin:4px 0 8px;">Aucun commentaire pour l\'instant.</p>';
    return;
  }
  container.innerHTML = comments.map(function(c) {
    var d = c.created_at ? c.created_at.substring(0,16).replace('T',' ') : '';
    return '<div style="padding:10px 0;border-bottom:1px solid var(--border);">' +
      '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px;">' +
      '<span style="font-weight:700;font-size:0.8rem;color:#1e40af;padding:2px 8px;background:#dbeafe;border-radius:12px;">👤 ' + escHtml(c.auteur) + '</span>' +
      '<div style="display:flex;align-items:center;gap:8px;">' +
      '<span style="font-size:0.7rem;color:var(--text-muted);">' + escHtml(d) + '</span>' +
      '<button onclick="_supprimerCommentaire(' + c.id + ',\'' + entite + '\',' + eid + ',\'' + urlPrefix + '\',' + inModal + ')" ' +
      'style="background:#fee2e2;color:#dc2626;border:1px solid #fecaca;border-radius:4px;padding:2px 6px;font-size:0.68rem;cursor:pointer;line-height:1.2;">✕</button>' +
      '</div></div>' +
      '<div class="cm-content" style="font-size:0.85rem;line-height:1.5;color:var(--text);">' + c.contenu + '</div>' +
      '</div>';
  }).join('');
}

function _supprimerCommentaire(cid, entite, eid, urlPrefix, inModal) {
  if (!confirm('Supprimer ce commentaire ?')) return;
  fetch(urlPrefix + 'api/commentaires/' + cid, { method: 'DELETE' })
    .then(function(){
      _chargerCommentaires(entite, eid, urlPrefix, inModal ? 'cm-list' : 'inline-cm-list', inModal);
    });
}

function _soumettreCommentaireMod(entite, eid, urlPrefix) {
  var auteur = (document.getElementById('cm-auteur').value || '').trim();
  if (!auteur) { alert('Votre nom est obligatoire.'); return; }
  var contenu = _cmQuill ? _cmQuill.root.innerHTML : '';
  if (!contenu || contenu === '<p><br></p>') { alert('Le commentaire ne peut pas être vide.'); return; }
  fetch(urlPrefix + 'api/commentaires/' + entite + '/' + eid, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({auteur: auteur, contenu: contenu})
  }).then(function(r){ return r.json(); })
    .then(function(data){
      if (data.ok) {
        document.getElementById('cm-auteur').value = '';
        if (_cmQuill) _cmQuill.setContents([]);
        _chargerCommentaires(entite, eid, urlPrefix, 'cm-list', true);
      } else { alert(data.error || 'Erreur'); }
    });
}

function soumettreCommentaireInline(entite, eid, urlPrefix) {
  var auteur = (document.getElementById('inline-cm-auteur').value || '').trim();
  if (!auteur) { alert('Votre nom est obligatoire.'); return; }
  var contenu = _inlineCmQuill ? _inlineCmQuill.root.innerHTML : '';
  if (!contenu || contenu === '<p><br></p>') { alert('Le commentaire ne peut pas être vide.'); return; }
  fetch(urlPrefix + 'api/commentaires/' + entite + '/' + eid, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({auteur: auteur, contenu: contenu})
  }).then(function(r){ return r.json(); })
    .then(function(data){
      if (data.ok) {
        document.getElementById('inline-cm-auteur').value = '';
        if (_inlineCmQuill) _inlineCmQuill.setContents([]);
        _chargerCommentaires(entite, eid, urlPrefix, 'inline-cm-list', false);
      } else { alert(data.error || 'Erreur'); }
    });
}

// ─── PIECES JOINTES ──────────────────────────────────────────────────────────
function _formatTaille(octets) {
  if (octets < 1024) return octets + ' o';
  if (octets < 1024 * 1024) return Math.round(octets / 1024) + ' Ko';
  return (octets / (1024 * 1024)).toFixed(1) + ' Mo';
}

var _pjEntite = null, _pjEntiteId = null, _pjUrlPrefix = '';

function ouvrirPjModal(entite, id, nom, urlPrefix) {
  _pjEntite = entite;
  _pjEntiteId = id;
  _pjUrlPrefix = urlPrefix || '';
  openModal('📎 Pièces jointes — ' + nom,
    '<div id="pj-modal-list" style="min-height:40px;margin-bottom:16px;"></div>' +
    '<div style="display:flex;gap:8px;align-items:center;padding-top:12px;border-top:1px solid var(--border);">' +
    '<input type="file" id="pj-modal-input" style="flex:1;font-size:0.82rem;">' +
    '<button class="btn btn-primary btn-sm" onclick="uploadPjModal()">📎 Joindre</button>' +
    '</div>' +
    '<div class="form-actions"><button type="button" class="btn btn-secondary" onclick="closeModal()">Fermer</button></div>');
  _chargerPjModal();
}

function _chargerPjModal() {
  var container = document.getElementById('pj-modal-list');
  if (!container) return;
  container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;">Chargement…</p>';
  fetch(_pjUrlPrefix + 'api/pieces-jointes/' + _pjEntite + '/' + _pjEntiteId)
    .then(function(r){ return r.json(); })
    .then(function(pjs){ _renderPjModal(pjs); });
}

function _renderPjModal(pjs) {
  var container = document.getElementById('pj-modal-list');
  if (!container) return;
  if (!pjs.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;font-style:italic;margin:0 0 4px;">Aucune pièce jointe.</p>';
    return;
  }
  container.innerHTML = pjs.map(function(pj) {
    return '<div style="display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid var(--border);">' +
      '<a href="' + _pjUrlPrefix + 'api/pieces-jointes/' + pj.id + '/download"' +
      ' style="flex:1;font-size:0.85rem;color:var(--primary);text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" target="_blank">📎 ' + escHtml(pj.nom_original) + '</a>' +
      '<span style="font-size:0.72rem;color:var(--text-muted);white-space:nowrap;">' + _formatTaille(pj.taille) + '</span>' +
      '<button onclick="supprimerPjModal(' + pj.id + ')"' +
      ' style="background:#fee2e2;color:#dc2626;border:1px solid #fecaca;border-radius:4px;padding:2px 6px;font-size:0.7rem;cursor:pointer;line-height:1.2;">✕</button>' +
      '</div>';
  }).join('');
}

function uploadPjModal() {
  var input = document.getElementById('pj-modal-input');
  if (!input || !input.files.length) { alert('Sélectionnez un fichier.'); return; }
  var file = input.files[0];
  if (file.size > 10 * 1024 * 1024) { alert('Fichier trop volumineux (10 Mo max).'); return; }
  var fd = new FormData();
  fd.append('fichier', file);
  fetch(_pjUrlPrefix + 'api/pieces-jointes/' + _pjEntite + '/' + _pjEntiteId, { method: 'POST', body: fd })
    .then(function(r){ return r.json(); })
    .then(function(data) {
      if (data.ok) { input.value = ''; _chargerPjModal(); }
      else { alert(data.error || 'Erreur lors de l\'upload.'); }
    });
}

function supprimerPjModal(pjId) {
  if (!confirm('Supprimer cette pièce jointe ?')) return;
  fetch(_pjUrlPrefix + 'api/pieces-jointes/' + pjId, { method: 'DELETE' })
    .then(function(){ _chargerPjModal(); });
}

function _copierFallback(url, cb) {
  var el = document.createElement('textarea');
  el.value = url;
  el.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none;';
  document.body.appendChild(el);
  el.focus();
  el.select();
  try { document.execCommand('copy'); if (cb) cb(); }
  catch(e) { prompt('Copiez ce lien :', url); }
  document.body.removeChild(el);
}
