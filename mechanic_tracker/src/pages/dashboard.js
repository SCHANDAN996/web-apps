/**
 * Dashboard page — Money at Risk, stats, urgent alerts
 */
import { getDashboardStats } from '../lib/store.js';
import { formatCurrency } from '../lib/currency.js';
import { getDeadlineInfo, getCardUrgencyClass } from '../lib/notifications.js';

export async function renderDashboard(container) {
  container.innerHTML = `<div style="text-align:center;padding:48px;"><div class="skeleton" style="width:60%;height:40px;margin:0 auto 16px;"></div><div class="skeleton" style="height:100px;margin-bottom:12px;"></div><div class="skeleton" style="height:20px;width:80%;margin:0 auto;"></div></div>`;

  const stats = await getDashboardStats();

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <div class="subtitle">Track your core deposits</div>
      </div>
      <div style="font-size:13px; color:var(--text-muted);">${new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</div>
    </div>

    <!-- Hero Card -->
    <div class="card-hero">
      <div class="hero-label">💰 Money at Risk</div>
      <div class="hero-value">${formatCurrency(stats.moneyAtRisk)}</div>
      <div class="hero-sub">${stats.pendingReturns} part${stats.pendingReturns !== 1 ? 's' : ''} awaiting return or refund</div>
    </div>

    <!-- Stats Grid -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-value">${stats.totalParts}</div>
        <div class="stat-label">Total</div>
      </div>
      <div class="stat-card stat-danger">
        <div class="stat-value">${stats.pendingReturns}</div>
        <div class="stat-label">Pending</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-value">${formatCurrency(stats.refundedThisMonth).replace(/\.\d+/, '')}</div>
        <div class="stat-label">Recovered</div>
      </div>
    </div>

    <!-- Urgent Alerts -->
    ${stats.urgentParts.length > 0 ? `
      <div class="section-title">🚨 Urgent — Return Within 48h</div>
      <div id="urgent-list"></div>
    ` : ''}

    <!-- Upcoming -->
    <div class="section-title">📅 Upcoming Deadlines</div>
    <div id="upcoming-list"></div>

    ${stats.upcomingParts.length === 0 ? `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
        <h3>All Clear!</h3>
        <p>No pending core returns. Add parts to start tracking.</p>
      </div>
    ` : ''}
  `;

  // Render urgent cards
  const urgentList = document.getElementById('urgent-list');
  if (urgentList) {
    stats.urgentParts.forEach(part => {
      urgentList.appendChild(makeQuickCard(part));
    });
  }

  // Render upcoming
  const upcomingList = document.getElementById('upcoming-list');
  if (upcomingList) {
    const upcoming = stats.upcomingParts.filter(p => !stats.urgentParts.find(u => u.id === p.id));
    upcoming.forEach(part => {
      upcomingList.appendChild(makeQuickCard(part));
    });
  }
}

function makeQuickCard(part) {
  const dl = getDeadlineInfo(part.return_deadline);
  const urgency = getCardUrgencyClass(part.return_deadline, part.status);
  const div = document.createElement('div');
  div.className = `part-card ${urgency}`;
  div.innerHTML = `
    <div class="part-card-header">
      <div class="part-card-title">${esc(part.part_name)}</div>
      <div class="part-card-fee">${formatCurrency(part.core_fee)}</div>
    </div>
    <div class="part-card-meta">
      <span>📦 ${esc(part.vendor_name || '')}</span>
      <span class="part-card-deadline ${dl.class}">📅 ${dl.text}</span>
      <span class="status-badge ${part.status.toLowerCase()}">${part.status}</span>
    </div>
  `;
  div.addEventListener('click', () => { window.location.hash = '#/tracker'; });
  return div;
}

function esc(s) { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
