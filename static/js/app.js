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
