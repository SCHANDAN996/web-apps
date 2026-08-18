/**
 * Settings page — vendors CRUD, notifications, subscription
 */
import { getVendors, addVendor, updateVendor, deleteVendor } from '../lib/store.js';
import { isPro, setPro, showUpgradePrompt } from '../lib/pro.js';
import { openModal, closeModal } from '../components/modal.js';

export async function renderSettings(container) {
  const vendors = await getVendors();
  const proStatus = isPro();

  container.innerHTML = `
    <div class="page-header"><div><h1>Settings</h1><div class="subtitle">Manage your shop</div></div></div>

    <!-- Subscription -->
    <div class="section-title">Subscription</div>
    <div class="card" style="margin-bottom:20px; ${proStatus ? 'border-left:4px solid var(--success);' : 'border-left:4px solid var(--warning);'}">
      <div style="display:flex; align-items:center; justify-content:space-between;">
        <div>
          <div style="font-size:15px; font-weight:700;">${proStatus ? '⭐ Pro Plan Active' : '🔒 Free Plan'}</div>
          <div style="font-size:13px; color:var(--text-secondary); margin-top:4px;">
            ${proStatus ? 'Unlimited parts, OCR scanning, priority support' : '5 parts limit, no OCR scanning'}
          </div>
        </div>
        ${proStatus
          ? `<button class="btn btn-sm btn-ghost" id="btn-cancel-pro" style="color:var(--danger);">Cancel</button>`
          : `<button class="btn btn-sm btn-primary" id="btn-upgrade-settings">Upgrade</button>`
        }
      </div>
    </div>

    <!-- Vendors -->
    <div class="section-title">Vendors <button class="btn btn-sm btn-secondary" id="btn-add-vendor" style="margin-left:auto;">+ Add</button></div>
    <div id="vendor-list">
      ${vendors.length === 0 ? '<div style="color:var(--text-muted);font-size:14px;padding:16px 0;">No vendors yet. Add your first supplier.</div>' : ''}
      ${vendors.map(v => `
        <div class="vendor-item" data-id="${v.id}">
          <div class="vendor-info">
            <div class="vendor-name">${esc(v.name)}</div>
            <div class="vendor-policy">${v.return_policy_days} day return policy${v.contact ? ` • ${esc(v.contact)}` : ''}</div>
          </div>
          <div class="vendor-actions">
            <button class="btn btn-icon btn-ghost btn-edit-vendor" data-id="${v.id}" title="Edit">✏️</button>
            <button class="btn btn-icon btn-ghost btn-del-vendor" data-id="${v.id}" title="Delete">🗑️</button>
          </div>
        </div>
      `).join('')}
    </div>

    <!-- Notifications -->
    <div class="section-title" style="margin-top:28px;">Notifications</div>
    <div class="settings-item" id="notif-toggle-item">
      <div class="settings-item-left">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px;"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
        <div>
          <div class="settings-item-label">Deadline Alerts</div>
          <div class="settings-item-desc">Get notified 48h before return deadline</div>
        </div>
      </div>
      <label class="toggle">
        <input type="checkbox" id="notif-toggle" ${Notification.permission === 'granted' ? 'checked' : ''} />
        <span class="toggle-slider"></span>
      </label>
    </div>

    <!-- About -->
    <div class="section-title" style="margin-top:28px;">About</div>
    <div class="settings-item" style="cursor:default;">
      <div class="settings-item-left">
        <div>
          <div class="settings-item-label">Core Return Tracker</div>
          <div class="settings-item-desc">Version 1.0.0 • Built with ❤️ for mechanics</div>
        </div>
      </div>
    </div>
    <div class="settings-item" id="btn-export-csv" style="margin-top:4px;">
      <div class="settings-item-left">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        <div>
          <div class="settings-item-label">Export Data (CSV)</div>
          <div class="settings-item-desc">Download all parts as spreadsheet</div>
        </div>
      </div>
    </div>
  `;

  // Event: Upgrade / Cancel Pro
  document.getElementById('btn-upgrade-settings')?.addEventListener('click', showUpgradePrompt);
  document.getElementById('btn-cancel-pro')?.addEventListener('click', () => {
    setPro(false);
    showToast('Pro cancelled. You\'re on the free plan.', 'warning');
    renderSettings(container);
  });

  // Event: Notification toggle
  document.getElementById('notif-toggle')?.addEventListener('change', async (e) => {
    if (e.target.checked) {
      const perm = await Notification.requestPermission();
      if (perm !== 'granted') { e.target.checked = false; showToast('Notification permission denied', 'error'); }
      else showToast('Notifications enabled', 'success');
    }
  });

  // Event: Add vendor
  document.getElementById('btn-add-vendor')?.addEventListener('click', () => showVendorModal(null, container));

  // Event: Edit vendor
  container.querySelectorAll('.btn-edit-vendor').forEach(btn => {
    btn.addEventListener('click', () => {
      const v = vendors.find(x => x.id === btn.dataset.id);
      if (v) showVendorModal(v, container);
    });
  });

  // Event: Delete vendor
  container.querySelectorAll('.btn-del-vendor').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (confirm('Delete this vendor?')) {
        await deleteVendor(btn.dataset.id);
        showToast('Vendor deleted', 'success');
        renderSettings(container);
      }
    });
  });

  // Event: Export CSV
  document.getElementById('btn-export-csv')?.addEventListener('click', exportCSV);

  // Listen for pro changes
  window.addEventListener('pro-changed', () => renderSettings(container), { once: true });
}

function showVendorModal(vendor, pageContainer) {
  const isEdit = !!vendor;
  openModal(`
    <h2>${isEdit ? 'Edit' : 'Add'} Vendor</h2>
    <form id="vendor-form">
      <div class="form-group">
        <label class="form-label">Vendor Name *</label>
        <input type="text" class="form-input" id="v-name" value="${esc(vendor?.name || '')}" placeholder="e.g. AutoZone" required />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Contact</label>
          <input type="text" class="form-input" id="v-contact" value="${esc(vendor?.contact || '')}" placeholder="Phone or email" />
        </div>
        <div class="form-group">
          <label class="form-label">Return Policy (days)</label>
          <input type="number" class="form-input" id="v-policy" value="${vendor?.return_policy_days || 30}" min="1" max="365" />
        </div>
      </div>
      <button type="submit" class="btn btn-primary btn-block" style="margin-top:8px;">${isEdit ? 'Save Changes' : 'Add Vendor'}</button>
      <button type="button" class="btn btn-ghost btn-block" id="btn-cancel-vendor" style="margin-top:4px;">Cancel</button>
    </form>
  `);

  document.getElementById('btn-cancel-vendor').addEventListener('click', closeModal);
  document.getElementById('vendor-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      name: document.getElementById('v-name').value.trim(),
      contact: document.getElementById('v-contact').value.trim(),
      return_policy_days: parseInt(document.getElementById('v-policy').value) || 30,
    };
    if (isEdit) await updateVendor(vendor.id, data);
    else await addVendor(data);
    closeModal();
    showToast(isEdit ? 'Vendor updated' : 'Vendor added', 'success');
    renderSettings(pageContainer);
  });
}

async function exportCSV() {
  const { getParts } = await import('../lib/store.js');
  const parts = await getParts('All');
  const headers = ['Part Name', 'SKU', 'Core Fee', 'Status', 'Vendor', 'Purchase Date', 'Deadline', 'Notes'];
  const rows = parts.map(p => [p.part_name, p.sku, p.core_fee, p.status, p.vendor_name, p.purchase_date, p.return_deadline, p.notes]);
  const csv = [headers, ...rows].map(r => r.map(c => `"${(c || '').toString().replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `core-returns-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  showToast('CSV exported!', 'success');
}

function showToast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

function esc(s) { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
