/**
 * Active Tracker page — filtered parts list with status updates
 */
import { getParts, updatePartStatus } from '../lib/store.js';
import { renderPartCard } from '../components/part-card.js';
import { isPro, showUpgradePrompt, getPartLimit } from '../lib/pro.js';

let currentFilter = 'All';

export async function renderTracker(container) {
  container.innerHTML = `
    <div class="page-header"><div><h1>Active Tracker</h1><div class="subtitle">Manage your core returns</div></div></div>
    <div class="filter-tabs" id="filter-tabs"></div>
    <div id="parts-list"></div>
  `;

  renderFilters();
  await loadParts();
}

function renderFilters() {
  const tabs = ['All', 'Installed', 'Bagged', 'Returned', 'Refunded'];
  const container = document.getElementById('filter-tabs');
  if (!container) return;
  container.innerHTML = tabs.map(t =>
    `<button class="filter-tab${t === currentFilter ? ' active' : ''}" data-filter="${t}">${t}</button>`
  ).join('');

  container.querySelectorAll('.filter-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      currentFilter = btn.dataset.filter;
      renderFilters();
      loadParts();
    });
  });
}

async function loadParts() {
  const listEl = document.getElementById('parts-list');
  if (!listEl) return;

  listEl.innerHTML = '<div class="skeleton" style="height:80px;margin-bottom:10px;"></div>'.repeat(3);

  const parts = await getParts(currentFilter);
  listEl.innerHTML = '';

  if (parts.length === 0) {
    listEl.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
        <h3>No Parts Found</h3>
        <p>${currentFilter === 'All' ? 'Add your first part to start tracking core returns.' : `No parts with status "${currentFilter}".`}</p>
        <a href="#/add" class="btn btn-primary btn-sm">+ Add Part</a>
      </div>
    `;
    return;
  }

  const limit = getPartLimit();
  const visibleParts = parts.slice(0, limit);
  const hiddenCount = Math.max(0, parts.length - limit);

  const wrapper = document.createElement('div');
  wrapper.style.position = 'relative';

  visibleParts.forEach((part, i) => {
    part._index = i;
    const card = renderPartCard(part, handleStatusChange);
    wrapper.appendChild(card);
  });

  // Show upgrade overlay if free user has more parts
  if (hiddenCount > 0) {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'text-align:center; padding:32px 16px; margin-top:8px;';
    overlay.innerHTML = `
      <div style="font-size:36px; margin-bottom:8px;">🔒</div>
      <h3 style="font-size:18px; font-weight:800; margin-bottom:8px;">${hiddenCount} More Part${hiddenCount > 1 ? 's' : ''} Hidden</h3>
      <p style="color:var(--text-secondary); font-size:14px; margin-bottom:16px;">Upgrade to Pro to see all your tracked parts.</p>
      <button class="btn btn-primary" id="btn-upgrade-tracker">Unlock Pro</button>
    `;
    wrapper.appendChild(overlay);
    setTimeout(() => {
      document.getElementById('btn-upgrade-tracker')?.addEventListener('click', () => {
        showUpgradePrompt();
      });
    }, 0);
  }

  listEl.appendChild(wrapper);
}

async function handleStatusChange(partId, newStatus, oldStatus) {
  try {
    await updatePartStatus(partId, newStatus, oldStatus);
    showToast(`Status updated to ${newStatus}`, 'success');
    await loadParts();
  } catch (err) {
    showToast('Failed to update status', 'error');
  }
}

function showToast(msg, type) {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}
