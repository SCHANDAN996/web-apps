/**
 * Modal utility
 */
export function openModal(html) {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('open');
  overlay.innerHTML = `<div class="modal-content">${html}</div>`;
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
}

export function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.remove('open');
  overlay.innerHTML = '';
}
