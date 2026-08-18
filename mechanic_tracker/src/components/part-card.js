/**
 * Part card component — renders a single part in the tracker list
 */
import { getDeadlineInfo, getCardUrgencyClass } from '../lib/notifications.js';
import { formatCurrency } from '../lib/currency.js';

export function renderPartCard(part, onStatusChange) {
  const urgency = getCardUrgencyClass(part.return_deadline, part.status);
  const deadline = getDeadlineInfo(part.return_deadline);
  const statusClass = part.status.toLowerCase();

  const nextStatuses = {
    'Installed': 'Bagged',
    'Bagged': 'Returned',
    'Returned': 'Refunded',
    'Refunded': null
  };
  const nextStatus = nextStatuses[part.status];

  const card = document.createElement('div');
  card.className = `part-card ${urgency}`;
  card.style.animationDelay = `${(part._index || 0) * 0.05}s`;
  card.innerHTML = `
    <div class="part-card-header">
      <div>
        <div class="part-card-title">${esc(part.part_name)}</div>
        <span class="status-badge ${statusClass}">${part.status}</span>
      </div>
      <div class="part-card-fee">${formatCurrency(part.core_fee)}</div>
    </div>
    <div class="part-card-meta">
      ${part.sku ? `<span>SKU: ${esc(part.sku)}</span>` : ''}
      ${part.vendor_name ? `<span>📦 ${esc(part.vendor_name)}</span>` : ''}
      <span class="part-card-deadline ${deadline.class}">📅 ${deadline.text}</span>
    </div>
    ${nextStatus ? `<div style="margin-top:10px;">
      <button class="btn btn-sm btn-secondary part-status-btn" data-id="${part.id}" data-next="${nextStatus}">
        Mark as ${nextStatus} →
      </button>
    </div>` : ''}
  `;

  const btn = card.querySelector('.part-status-btn');
  if (btn && onStatusChange) {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      onStatusChange(part.id, btn.dataset.next, part.status);
    });
  }

  return card;
}

function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}
