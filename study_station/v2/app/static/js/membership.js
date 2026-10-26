/* The server owns the trial clock. No entitlement is stored in localStorage. */
(function () {
  'use strict';
  let priorScope = null;
  let renewal = null;
  let scopeEpoch = 0;
  window.SSMembershipRenew = function () {
    const bridge = window.StudyStationMembership;
    if (!bridge || !bridge.required()) return Promise.resolve(false);
    if (renewal && renewal.epoch === scopeEpoch) return renewal.promise;
    const epoch = scopeEpoch;
    const promise = fetch('/api/v1/membership/lease', {credentials: 'same-origin', cache: 'no-store'})
      .then(async response => {
        if (!response.ok) {
          if (epoch === scopeEpoch && (response.status === 401 || response.status === 402)) await bridge.clear();
          return false;
        }
        const value = await response.json();
        if (epoch !== scopeEpoch) return false;
        const stored = await bridge.storeLease(value.lease);
        if (epoch !== scopeEpoch) { await bridge.clear(); return false; }
        return !!stored.ok;
      }).catch(() => false).finally(() => { if (renewal && renewal.epoch === epoch) renewal = null; });
    renewal = {epoch, promise};
    return promise;
  };
  window.addEventListener('workspace-scope-changed', function () {
    const bridge = window.StudyStationMembership;
    if (!bridge) return;
    const scope = window.SSWorkspaceScope ? window.SSWorkspaceScope() : 'guest';
    if (scope === priorScope) return;
    priorScope = scope;
    const epoch = ++scopeEpoch;
    bridge.status().then(async state => {
      if (epoch !== scopeEpoch) return;
      const namespace = scope.indexOf('account:') === 0 ? scope.slice(8) : null;
      // A signed lease for this account remains valid across fresh documents.
      if (namespace && state.ok && state.namespace === namespace) return;
      if (!namespace || state.namespace !== namespace) await bridge.clear();
      if (namespace && epoch === scopeEpoch) return window.SSMembershipRenew();
    }).catch(() => {});
  });
  window.SSMembershipInit = function (root) {
    if (window.SSPlayBillingInit) window.SSPlayBillingInit(root || document);
    const panel = (root || document).querySelector('#membershipPanel');
    if (!panel || panel.dataset.ready) return;
    panel.dataset.ready = '1';
    const line = panel.querySelector('[data-membership-status]');
    const logout=panel.querySelector('[data-account-logout]');if(logout)logout.addEventListener('click',async()=>{logout.disabled=true;try{const r=await fetch('/api/v1/classroom/logout',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});if(!r.ok)throw Error('logout');if(window.SSWorkspaceForgetAccount)SSWorkspaceForgetAccount();window.dispatchEvent(new Event('workspace-scope-changed'));if(window.StudyStationMembership)await StudyStationMembership.clear();if(window.StudyStationAuth&&StudyStationAuth.signOut)await StudyStationAuth.signOut();location.assign('/login');}catch(e){line.textContent=tr('membership_error');logout.disabled=false;}});
    const start = panel.querySelector('[data-membership-start]');
    const words = JSON.parse(document.getElementById('ss-boot').textContent).t || {};
    const tr = key => words[key] || key;
    function render(value) {
      panel.hidden = !value.enabled;
      if (window.SSMembershipCheckout) window.SSMembershipCheckout(panel, value);
      start.hidden = value.state !== 'available';
      line.textContent = tr('membership_' + value.state);
      const note=panel.querySelector('[data-membership-payment-note]');if(note)note.hidden=value.state!=='expired';
      const checkout=panel.querySelector('[data-membership-checkout]');if(checkout)checkout.hidden=value.state!=='expired';
      if(value.state==='paid'&&value.paid_until)line.textContent+=' '+new Date(value.paid_until).toLocaleDateString(document.documentElement.lang==='hi'?'hi-IN':'en-IN');
      if (value.state === 'trial') {
        const language = document.documentElement.lang === 'hi' ? 'hi-IN' : 'en-IN';
        line.textContent += ' ' + new Date(value.trial_ends_at).toLocaleDateString(language,{day:'numeric',month:'long',year:'numeric'}) + ' · ' + Math.ceil(value.remaining_seconds / 86400) + ' ' + tr('membership_days_left');
      }
    }
    async function request(method) {
      const response = await fetch('/api/v1/membership/' + (method === 'POST' ? 'start' : 'status'), {
        method, credentials: 'same-origin', cache: 'no-store',
        ...(method === 'POST' ? {headers: {'Content-Type': 'application/json'}, body: JSON.stringify({confirm: true})} : {})
      });
      if (!response.ok) throw new Error('membership_unavailable');
      render(await response.json());
      if (method === 'POST') await window.SSMembershipRenew();
    }
    start.addEventListener('click', async () => {
      start.disabled = true;
      try { await request('POST'); }
      catch (_) { line.textContent = tr('membership_error'); }
      finally { start.disabled = false; }
    });
    panel.hidden=false;line.textContent=tr('membership_loading');
    const retry=document.createElement('button');retry.type='button';retry.className='btn btn-secondary';retry.textContent=tr('membership_access_retry');retry.hidden=true;panel.append(retry);
    function load(){retry.disabled=true;return request('GET').then(()=>{retry.hidden=true;}).catch(()=>{panel.hidden=false;line.textContent=tr('membership_error');retry.hidden=false;}).finally(()=>{retry.disabled=false;});}
    retry.addEventListener('click',load);load();
    fetch('/api/v1/classroom/me',{credentials:'same-origin',cache:'no-store'}).then(r=>r.json()).then(d=>{if(!panel.isConnected||!d.account)return;const identity=document.createElement('p');identity.className='muted';identity.textContent=(d.account.name||d.account.username)+' · '+d.account.username;panel.prepend(identity);}).catch(()=>{});
  };
}());

