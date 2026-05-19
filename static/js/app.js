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
