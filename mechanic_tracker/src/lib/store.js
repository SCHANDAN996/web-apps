/**
 * Local data store — works without Supabase for demo/development.
 * When Supabase is configured, all ops go through the cloud DB instead.
 */
import { supabase, isSupabaseReady } from './supabase.js';

const VENDORS_KEY = 'mcrt_vendors';
const PARTS_KEY = 'mcrt_parts';

// ──── Seed demo data on first run ────
function seedIfEmpty() {
  if (!localStorage.getItem(VENDORS_KEY)) {
    const vendors = [
      { id: 'v1', name: 'AutoZone', contact: '555-0101', return_policy_days: 30 },
      { id: 'v2', name: "O'Reilly Auto Parts", contact: '555-0202', return_policy_days: 45 },
      { id: 'v3', name: 'NAPA Auto Parts', contact: '555-0303', return_policy_days: 30 },
      { id: 'v4', name: 'Advance Auto Parts', contact: '555-0404', return_policy_days: 60 },
    ];
    localStorage.setItem(VENDORS_KEY, JSON.stringify(vendors));
  }
  if (!localStorage.getItem(PARTS_KEY)) {
    const today = new Date();
    const d = (offset) => { const dt = new Date(today); dt.setDate(dt.getDate() + offset); return dt.toISOString().split('T')[0]; };
    const parts = [
      { id: 'p1', vendor_id: 'v1', vendor_name: 'AutoZone', part_name: 'Alternator - Duralast Gold', sku: 'DLG-4872', core_fee: 65.00, status: 'Installed', purchase_date: d(-20), return_deadline: d(10), notes: '' },
      { id: 'p2', vendor_id: 'v2', vendor_name: "O'Reilly Auto Parts", part_name: 'Battery - SuperStart Platinum', sku: 'SSP-78DT', core_fee: 22.00, status: 'Bagged', purchase_date: d(-25), return_deadline: d(1), notes: 'Customer car: Blue Honda Civic' },
      { id: 'p3', vendor_id: 'v3', vendor_name: 'NAPA Auto Parts', part_name: 'Starter Motor - Remy', sku: 'RMY-26632', core_fee: 45.00, status: 'Installed', purchase_date: d(-5), return_deadline: d(25), notes: '' },
      { id: 'p4', vendor_id: 'v1', vendor_name: 'AutoZone', part_name: 'Brake Caliper - Cardone', sku: 'CDN-19B2601', core_fee: 35.00, status: 'Returned', purchase_date: d(-40), return_deadline: d(-10), notes: 'Returned 2 days ago' },
      { id: 'p5', vendor_id: 'v4', vendor_name: 'Advance Auto Parts', part_name: 'Power Steering Pump', sku: 'AAP-PS553', core_fee: 55.00, status: 'Refunded', purchase_date: d(-50), return_deadline: d(-20), notes: 'Refund received $55' },
      { id: 'p6', vendor_id: 'v2', vendor_name: "O'Reilly Auto Parts", part_name: 'Water Pump - GMB', sku: 'GMB-130-2060', core_fee: 18.00, status: 'Installed', purchase_date: d(-3), return_deadline: d(42), notes: '' },
    ];
    localStorage.setItem(PARTS_KEY, JSON.stringify(parts));
  }
}
seedIfEmpty();

// ──── Generic helpers ────
function getLocal(key) { try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch { return []; } }
function setLocal(key, data) { localStorage.setItem(key, JSON.stringify(data)); }
function uid() { return 'id_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }

// ──────────────────────── VENDORS ────────────────────────
export async function getVendors() {
  if (isSupabaseReady()) {
    const { data } = await supabase.from('vendors').select('*').order('name');
    return data || [];
  }
  return getLocal(VENDORS_KEY);
}

export async function addVendor(vendor) {
  if (isSupabaseReady()) {
    const { data, error } = await supabase.from('vendors').insert(vendor).select().single();
    if (error) throw error;
    return data;
  }
  const vendors = getLocal(VENDORS_KEY);
  const newVendor = { id: uid(), ...vendor };
  vendors.push(newVendor);
  setLocal(VENDORS_KEY, vendors);
  return newVendor;
}

export async function updateVendor(id, updates) {
  if (isSupabaseReady()) {
    const { data, error } = await supabase.from('vendors').update(updates).eq('id', id).select().single();
    if (error) throw error;
    return data;
  }
  const vendors = getLocal(VENDORS_KEY);
  const idx = vendors.findIndex(v => v.id === id);
  if (idx >= 0) { vendors[idx] = { ...vendors[idx], ...updates }; setLocal(VENDORS_KEY, vendors); }
  return vendors[idx];
}

export async function deleteVendor(id) {
  if (isSupabaseReady()) {
    const { error } = await supabase.from('vendors').delete().eq('id', id);
    if (error) throw error;
    return;
  }
  const vendors = getLocal(VENDORS_KEY).filter(v => v.id !== id);
  setLocal(VENDORS_KEY, vendors);
}

// ──────────────────────── PARTS ────────────────────────
export async function getParts(filter = 'All') {
  if (isSupabaseReady()) {
    let q = supabase.from('parts').select('*, vendors(name)').order('return_deadline', { ascending: true });
    if (filter !== 'All') q = q.eq('status', filter);
    const { data } = await q;
    return (data || []).map(p => ({ ...p, vendor_name: p.vendors?.name || '' }));
  }
  let parts = getLocal(PARTS_KEY);
  if (filter !== 'All') parts = parts.filter(p => p.status === filter);
  return parts.sort((a, b) => new Date(a.return_deadline) - new Date(b.return_deadline));
}

export async function addPart(part) {
  if (isSupabaseReady()) {
    const { data, error } = await supabase.from('parts').insert(part).select().single();
    if (error) throw error;
    return data;
  }
  const parts = getLocal(PARTS_KEY);
  const vendors = getLocal(VENDORS_KEY);
  const vendor = vendors.find(v => v.id === part.vendor_id);
  const purchaseDate = new Date(part.purchase_date || new Date());
  const policyDays = vendor?.return_policy_days || 30;
  const deadline = new Date(purchaseDate);
  deadline.setDate(deadline.getDate() + policyDays);

  const newPart = {
    id: uid(),
    ...part,
    vendor_name: vendor?.name || '',
    return_deadline: part.return_deadline || deadline.toISOString().split('T')[0],
    status: part.status || 'Installed',
    created_at: new Date().toISOString()
  };
  parts.push(newPart);
  setLocal(PARTS_KEY, parts);
  return newPart;
}

export async function updatePartStatus(id, newStatus, oldStatus) {
  if (isSupabaseReady()) {
    const { error } = await supabase.from('parts').update({ status: newStatus, updated_at: new Date().toISOString() }).eq('id', id);
    if (error) throw error;
    // Log transaction
    await supabase.from('transactions').insert({ part_id: id, action: 'status_changed', old_status: oldStatus, new_status: newStatus });
    return;
  }
  const parts = getLocal(PARTS_KEY);
  const idx = parts.findIndex(p => p.id === id);
  if (idx >= 0) { parts[idx].status = newStatus; parts[idx].updated_at = new Date().toISOString(); setLocal(PARTS_KEY, parts); }
}

export async function deletePart(id) {
  if (isSupabaseReady()) {
    const { error } = await supabase.from('parts').delete().eq('id', id);
    if (error) throw error;
    return;
  }
  const parts = getLocal(PARTS_KEY).filter(p => p.id !== id);
  setLocal(PARTS_KEY, parts);
}

export async function getPartCount() {
  const parts = await getParts('All');
  return parts.length;
}

// ──────────────────────── STATS ────────────────────────
export async function getDashboardStats() {
  const parts = await getParts('All');
  const atRisk = parts.filter(p => ['Installed', 'Bagged'].includes(p.status));
  const moneyAtRisk = atRisk.reduce((sum, p) => sum + Number(p.core_fee), 0);
  const now = new Date();
  const urgent = atRisk.filter(p => {
    if (!p.return_deadline) return false;
    const dl = new Date(p.return_deadline);
    return (dl - now) / (1000 * 60 * 60) <= 48 && (dl - now) > 0;
  });
  const refundedThisMonth = parts.filter(p => {
    if (p.status !== 'Refunded') return false;
    const d = new Date(p.updated_at || p.created_at);
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  });
  const refundedAmount = refundedThisMonth.reduce((s, p) => s + Number(p.core_fee), 0);

  return {
    moneyAtRisk,
    totalParts: parts.length,
    pendingReturns: atRisk.length,
    refundedThisMonth: refundedAmount,
    urgentParts: urgent,
    upcomingParts: atRisk.slice(0, 10),
  };
}
