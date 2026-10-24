/* Prices and checkout come from Google Play. A purchased token alone never unlocks study. */
(function () {
  'use strict';
  let epoch = 0;
  const t = key => window.SS && SS.t && SS.t['play_billing_' + key] || '';
  function node(tag, text, className) {
    const value = document.createElement(tag);
    if (text) value.textContent = text;
    if (className) value.className = className;
    return value;
  }
  window.SSPlayBillingInit = function (root) {
    (root || document).querySelectorAll('[data-play-billing]').forEach(panel => {
      if (panel.dataset.playReady || !window.StudyStationBilling) return;
      panel.dataset.playReady = 'true';
      panel.hidden = false;
      const stamp = epoch;
      const bridge = window.StudyStationBilling;
      let busy = false;
      const status = node('p', t('loading'), 'muted');
      status.setAttribute('role', 'status');
      const choices = node('div', '', 'stack');
      const restore = node('button', t('restore'), 'btn btn-secondary');
      restore.type = 'button';
      restore.disabled = true;
      panel.replaceChildren(status, choices, restore);
      const current = () => stamp === epoch && panel.isConnected;
      function lock(value) {
        busy = value;
        panel.querySelectorAll('button').forEach(button => { button.disabled = value; });
      }
      async function process(result) {
        if (!current()) return;
        if (!result || !result.ok) {
          status.textContent = t(result && result.error === 'cancelled' ? 'cancelled' : 'unavailable');
          return;
        }
        if (result.alternative) {
          try {
            const response = await fetch('/api/v1/payments/google/alternative/start', {
              method: 'POST', credentials: 'same-origin', cache: 'no-store',
              headers: {'Content-Type': 'application/json'}, body: JSON.stringify(result.alternative)
            });
            const value = response.ok ? await response.json() : null;
            if (!current()) return;
            if (!value || typeof value.choice_id !== 'string' || !/^[A-Za-z0-9_-]{20,64}$/.test(value.choice_id) ||
                value.checkout_url !== '/membership?play_choice=' + value.choice_id) throw Error('invalid_checkout');
            // A full document installs the membership page's hosted-payment CSP.
            // No SDK token is placed in a URL or passed to another application.
            window.location.assign(value.checkout_url);
          } catch (_) { if (current()) status.textContent = t('unavailable'); }
          return;
        }
        const rows = Array.isArray(result.purchases) ? result.purchases.slice(0, 20) : [];
        let entitled = false, pending = false, failed = false;
        for (const purchase of rows) {
          if (!current()) return;
          if (purchase.state !== 'purchased') { pending = true; continue; }
          if (typeof purchase.purchaseToken !== 'string' || purchase.purchaseToken.length < 16 || purchase.purchaseToken.length > 16384) { failed = true; continue; }
          try {
            const response = await fetch('/api/v1/payments/google/verify', {
              method: 'POST', credentials: 'same-origin', cache: 'no-store',
              headers: {'Content-Type': 'application/json'}, body: JSON.stringify({purchase_token: purchase.purchaseToken})
            });
            const value = response.ok ? await response.json() : null;
            if (!current()) return;
            if (value && value.verified === true && value.entitled === true && value.acknowledged === true) entitled = true;
            else failed = true;
          } catch (_) { failed = true; }
        }
        if (!current()) return;
        if (entitled) {
          if (window.SSMembershipRenew) await window.SSMembershipRenew();
          if (!current()) return;
          status.textContent = t('success');
          window.dispatchEvent(new Event('ss-membership-updated'));
        } else status.textContent = t(pending ? 'pending' : failed ? 'verify_failed' : 'empty');
      }
      restore.addEventListener('click', async () => {
        if (busy || !current()) return;
        lock(true);
        try { await process(await bridge.restore()); }
        catch (_) { if (current()) status.textContent = t('unavailable'); }
        finally { if (current()) lock(false); }
      });
      (async () => {
        try {
          const response = await fetch('/api/v1/payments/google/config', {credentials: 'same-origin', cache: 'no-store'});
          const config = response.ok ? await response.json() : null;
          if (!current()) return;
          if (!config || !config.enabled) { status.textContent = t('unavailable'); return; }
          const result = await bridge.query(config);
          if (!current()) return;
          restore.disabled = false;
          if (!result || !result.ok || !Array.isArray(result.products) || !result.products.length) { status.textContent = t('unavailable'); return; }
          status.textContent = '';
          for (const product of result.products) {
            if (!['monthly', 'yearly'].includes(product.plan_id) || typeof product.price !== 'string' || !product.price) continue;
            const button = node('button', t('buy') + ' · ' + t(product.plan_id) + ' · ' + product.price, 'btn btn-primary');
            button.type = 'button';
            button.dataset.playPlan = product.plan_id;
            button.addEventListener('click', async () => {
              if (busy || !current()) return;
              // Call synchronously inside the trusted click to retain native user activation.
              const operation = bridge.purchase(product.plan_id);
              lock(true);
              try {
                let value = await operation;
                if (value && value.error === 'already_owned') value = await bridge.restore();
                await process(value);
              } catch (_) { if (current()) status.textContent = t('unavailable'); }
              finally { if (current()) lock(false); }
            });
            choices.appendChild(button);
          }
          if (!choices.children.length) status.textContent = t('unavailable');
        } catch (_) { if (current()) status.textContent = t('unavailable'); }
      })();
    });
  };
  window.addEventListener('ss-play-billing-ready', () => window.SSPlayBillingInit(document));
  window.addEventListener('workspace-scope-changed', () => {
    epoch++;
    document.querySelectorAll('[data-play-billing]').forEach(panel => { delete panel.dataset.playReady; });
    window.SSPlayBillingInit(document);
  });
})();
