/**
 * Pro subscription gate logic
 */
import { formatCurrency } from './currency.js';
const PRO_KEY = 'mcrt_pro_status';
const FREE_PART_LIMIT = 5;

export function isPro() {
  return localStorage.getItem(PRO_KEY) === 'true';
}

export function setPro(val) {
  localStorage.setItem(PRO_KEY, val ? 'true' : 'false');
}

export function canAddPart(currentCount) {
  if (isPro()) return true;
  return currentCount < FREE_PART_LIMIT;
}

export function getPartLimit() {
  return isPro() ? Infinity : FREE_PART_LIMIT;
}

export function showUpgradePrompt() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('open');
  overlay.innerHTML = `
    <div class="modal-content" style="text-align:center; padding: 32px 24px;">
      <div style="font-size:48px; margin-bottom:12px;">🔓</div>
      <h2>Unlock Pro</h2>
      <p style="color:var(--text-secondary); margin-bottom:24px;">
        Track unlimited parts, enable receipt OCR scanning, and never miss a core return deadline.
      </p>
      <div class="upgrade-price">${formatCurrency(19.99)}<span>/month</span></div>
      <p style="font-size:13px; color:var(--text-muted); margin:12px 0 24px;">7-day free trial • Cancel anytime</p>
      <button class="btn btn-primary btn-block" id="btn-start-trial">Start Free Trial</button>
      <button class="btn btn-ghost btn-block" id="btn-close-upgrade" style="margin-top:8px;">Maybe Later</button>
    </div>
  `;
  document.getElementById('btn-start-trial').addEventListener('click', () => {
    setPro(true);
    overlay.classList.remove('open');
    overlay.innerHTML = '';
    showToast('🎉 Pro activated! Enjoy unlimited tracking.', 'success');
    window.dispatchEvent(new Event('pro-changed'));
  });
  document.getElementById('btn-close-upgrade').addEventListener('click', () => {
    overlay.classList.remove('open');
    overlay.innerHTML = '';
  });
}

function showToast(msg, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
