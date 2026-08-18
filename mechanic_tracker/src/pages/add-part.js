/**
 * Add Part page — barcode scan, receipt OCR, manual form
 */
import { getVendors, addPart, getPartCount } from '../lib/store.js';
import { parseReceipt } from '../lib/ocr.js';
import { startBarcodeScanner } from '../lib/scanner.js';
import { canAddPart, isPro, showUpgradePrompt } from '../lib/pro.js';
import { getCurrencySymbol, formatCurrency } from '../lib/currency.js';

export async function renderAddPart(container) {
  const vendors = await getVendors();
  const count = await getPartCount();

  if (!canAddPart(count)) {
    container.innerHTML = `
      <div class="page-header"><div><h1>Add Part</h1></div></div>
      <div class="empty-state">
        <div style="font-size:48px; margin-bottom:12px;">🔒</div>
        <h3>Free Limit Reached</h3>
        <p>You've tracked ${count} parts. Upgrade to Pro for unlimited tracking.</p>
        <button class="btn btn-primary" id="btn-upgrade-add">Unlock Pro — ${formatCurrency(19.99)}/mo</button>
      </div>
    `;
    document.getElementById('btn-upgrade-add')?.addEventListener('click', showUpgradePrompt);
    return;
  }

  container.innerHTML = `
    <div class="page-header"><div><h1>Add Part</h1><div class="subtitle">Scan or manually add a core return</div></div></div>

    <!-- Scan Options -->
    <div class="scan-options">
      <button class="scan-btn" id="btn-scan-barcode">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="7" y1="8" x2="7" y2="16"/><line x1="11" y1="8" x2="11" y2="16"/><line x1="15" y1="8" x2="15" y2="16" stroke-width="2.5"/><line x1="19" y1="8" x2="19" y2="16" stroke-width="0.8"/></svg>
        Scan Barcode
      </button>
      <button class="scan-btn" id="btn-scan-receipt">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        Scan Receipt
      </button>
    </div>

    <!-- OCR Result Banner -->
    <div id="ocr-result" style="display:none;" class="card" style="margin-bottom:16px; border-left:4px solid var(--success);"></div>

    <!-- Receipt file input (hidden) -->
    <input type="file" id="receipt-file-input" accept="image/*" capture="environment" style="display:none;" />

    <!-- Manual Form -->
    <form id="add-part-form">
      <div class="form-group">
        <label class="form-label">Part Name *</label>
        <input type="text" class="form-input" id="inp-part-name" placeholder="e.g. Alternator - Duralast Gold" required />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">SKU / Part #</label>
          <input type="text" class="form-input" id="inp-sku" placeholder="e.g. DLG-4872" />
        </div>
        <div class="form-group">
          <label class="form-label">Core Fee (${getCurrencySymbol()}) *</label>
          <input type="number" class="form-input" id="inp-core-fee" placeholder="0.00" step="0.01" min="0" required />
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Vendor *</label>
        <select class="form-select" id="inp-vendor" required>
          <option value="">Select vendor...</option>
          ${vendors.map(v => `<option value="${v.id}" data-policy="${v.return_policy_days}">${esc(v.name)} (${v.return_policy_days}d return)</option>`).join('')}
        </select>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Purchase Date</label>
          <input type="date" class="form-input" id="inp-purchase-date" value="${new Date().toISOString().split('T')[0]}" />
        </div>
        <div class="form-group">
          <label class="form-label">Return Deadline</label>
          <input type="date" class="form-input" id="inp-deadline" readonly />
          <div class="form-hint">Auto-calculated from vendor policy</div>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Receipt Photo</label>
        <input type="file" class="form-input" id="inp-receipt-photo" accept="image/*" capture="environment" style="padding:8px;" />
      </div>
      <div class="form-group">
        <label class="form-label">Notes</label>
        <textarea class="form-textarea" id="inp-notes" placeholder="Customer name, vehicle info, etc."></textarea>
      </div>
      <div id="form-error" class="form-error" style="margin-bottom:12px;"></div>
      <button type="submit" class="btn btn-primary btn-block" id="btn-save-part">
        💾 Save Part
      </button>
    </form>
  `;

  // Auto-calculate deadline when vendor or date changes
  const vendorSel = document.getElementById('inp-vendor');
  const dateInp = document.getElementById('inp-purchase-date');
  const deadlineInp = document.getElementById('inp-deadline');

  function calcDeadline() {
    const opt = vendorSel.selectedOptions[0];
    const policy = opt?.dataset?.policy ? parseInt(opt.dataset.policy) : 30;
    const purchaseDate = new Date(dateInp.value || new Date());
    purchaseDate.setDate(purchaseDate.getDate() + policy);
    deadlineInp.value = purchaseDate.toISOString().split('T')[0];
  }
  vendorSel.addEventListener('change', calcDeadline);
  dateInp.addEventListener('change', calcDeadline);

  // Barcode scanner
  document.getElementById('btn-scan-barcode').addEventListener('click', async () => {
    try {
      await startBarcodeScanner((code) => {
        document.getElementById('inp-sku').value = code;
        showToast(`Barcode scanned: ${code}`, 'success');
      });
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Receipt OCR
  const receiptInput = document.getElementById('receipt-file-input');
  document.getElementById('btn-scan-receipt').addEventListener('click', () => {
    if (!isPro()) {
      showUpgradePrompt();
      return;
    }
    receiptInput.click();
  });

  receiptInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const resultDiv = document.getElementById('ocr-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<div style="display:flex;align-items:center;gap:8px;"><span class="spinner" style="border-color:var(--primary-glow);border-top-color:var(--primary);width:16px;height:16px;"></span> Scanning receipt...</div>';

    const result = await parseReceipt(file);
    if (result.success) {
      const d = result.extracted;
      if (d.totalCoreFee > 0) document.getElementById('inp-core-fee').value = d.totalCoreFee.toFixed(2);
      if (d.vendor) {
        // Try to match vendor
        const match = vendors.find(v => v.name.toLowerCase().includes(d.vendor.toLowerCase().slice(0, 8)));
        if (match) vendorSel.value = match.id;
      }
      resultDiv.innerHTML = `<div style="color:var(--success);font-weight:700;">✅ Receipt Scanned</div>
        <div style="font-size:13px;color:var(--text-secondary);margin-top:6px;">
          ${d.coreItems.length ? `Found ${d.coreItems.length} core charge(s): ${formatCurrency(d.totalCoreFee)}` : 'No core charges detected — fill in manually.'}
          ${d.vendor ? `<br>Vendor: ${d.vendor}` : ''}
          ${d.date ? `<br>Date: ${d.date}` : ''}
        </div>`;
      calcDeadline();
    } else {
      resultDiv.innerHTML = `<div style="color:var(--danger);">❌ ${result.error}</div>`;
    }
  });

  // Form submit
  document.getElementById('add-part-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-save-part');
    const errorEl = document.getElementById('form-error');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Saving...';
    errorEl.textContent = '';

    try {
      await addPart({
        part_name: document.getElementById('inp-part-name').value.trim(),
        sku: document.getElementById('inp-sku').value.trim(),
        core_fee: parseFloat(document.getElementById('inp-core-fee').value) || 0,
        vendor_id: vendorSel.value,
        purchase_date: dateInp.value,
        return_deadline: deadlineInp.value,
        notes: document.getElementById('inp-notes').value.trim(),
        status: 'Installed',
      });
      showToast('✅ Part saved successfully!', 'success');
      window.location.hash = '#/tracker';
    } catch (err) {
      errorEl.textContent = err.message || 'Failed to save part';
      btn.disabled = false;
      btn.innerHTML = '💾 Save Part';
    }
  });
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
