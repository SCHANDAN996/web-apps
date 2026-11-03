/* Explicit one-time checkout: browser website and opted-in direct APK only. */
(function () {
  'use strict';
  let configPromise;
  let scopeEpoch = 0;
  window.addEventListener('workspace-scope-changed', () => { scopeEpoch++; });
  const choiceId = () => new URLSearchParams(location.search).get('play_choice');
  // Old WebViews inject bridges after deferred scripts; their native UA marker
  // suppresses checkout immediately. This is presentation, never authorization.
  const nativeApp = () => /StudyStationApp\//.test(navigator.userAgent) ||
    !!(window.StudyStationAuth || window.StudyStationMembership || window.StudyStationBackup);
  const allowedCheckout = () => {
    if (!nativeApp()) return true;
    try {
      const bridge = window.StudyStationMembership;
      return !!bridge && typeof bridge.allowPayu === 'function' && bridge.allowPayu() === true;
    } catch (_) { return false; }
  };
  window.SSMembershipCheckout = async function (panel, membership) {
    const slot = panel.querySelector('[data-membership-checkout]');
    const requestedChoice = choiceId();
    if (!slot || (!allowedCheckout() && !requestedChoice) || !membership.enabled || slot.dataset.ready) return;
    const stamp = scopeEpoch;
    const current = () => panel.isConnected && stamp === scopeEpoch;
    const boot = JSON.parse(document.getElementById('ss-boot').textContent);
    slot.dataset.ready = '1';
    try {
      let playChoice = null;
      if (requestedChoice) {
        if (!/^[A-Za-z0-9_-]{20,64}$/.test(requestedChoice)) return;
        const response = await fetch('/api/v1/payments/google/alternative/checkout?choice_id=' + encodeURIComponent(requestedChoice), {credentials:'same-origin',cache:'no-store'});
        const value = response.ok ? await response.json() : null;
        if (!current() || !value || value.enabled !== true || value.choice_id !== requestedChoice ||
            !['monthly','yearly'].includes(value.plan_id) || !Array.isArray(value.states) || !value.states.length ||
            value.states.some(state => typeof state !== 'string' || !/^[A-Z ]{3,64}$/.test(state)) ||
            !(Date.parse(value.expires_at) > Date.now())) return;
        playChoice = value;
      }
      if (!configPromise) configPromise = fetch('/api/v1/payments/payu/config', {credentials:'same-origin', cache:'no-store'}).then(r => r.ok ? r.json() : {enabled:false});
      const config = await configPromise;
      if (!current() || (!allowedCheckout() && !playChoice) || !config.enabled || config.channel !== 'website') return;
      const words = boot.t || {};
      const tr = key => words[key] || key;
      function node(tag, text) { const e=document.createElement(tag); if (text) e.textContent=text; return e; }
      const note=panel.querySelector('[data-membership-payment-note]');
      if (note) note.textContent=tr('payu_no_renew');
      if (nativeApp() && !playChoice) {
        const bridge=window.StudyStationMembership;
        if (!bridge || typeof bridge.openPayuWebsite !== 'function') return;
        const controls=node('div');controls.className='membership-direct-actions';
        controls.append(node('p',tr('payu_same_account')));
        const open=node('button',tr('payu_open_website'));open.type='button';open.className='btn btn-primary';
        const refresh=node('button',tr('payu_refresh_access'));refresh.type='button';refresh.className='btn btn-secondary';
        const status=node('p');status.setAttribute('role','status');
        open.addEventListener('click',function(){
          if (!allowedCheckout()) return;
          // Native code owns the fixed URL and click validation. No token or URL
          // is passed across applications; the browser signs in independently.
          try { Promise.resolve(bridge.openPayuWebsite()).then(result=>{
            if(result===false||(result&&result.ok===false))status.textContent=tr('payu_error');
          }).catch(()=>{status.textContent=tr('payu_error');}); }
          catch (_) {status.textContent=tr('payu_error');}
        });
        refresh.addEventListener('click',()=>refreshAccess(panel,refresh));
        controls.append(open,refresh,status);slot.append(controls);return;
      }
      const form=node('form');form.className='membership-payment-form';
      form.append(node('h3',tr('payu_choose')));
      const planLabel=node('label',tr('payu_choose')),plans=node('select');plans.className='in';plans.name='plan_id';
      ['monthly','yearly'].forEach(id=>{const option=node('option',tr('payu_'+id));option.value=id;plans.append(option);});planLabel.append(plans);form.append(planLabel);
      let billingState = null;
      if (playChoice) {
        plans.value = playChoice.plan_id;plans.disabled = true;
        const stateLabel = node('label',tr('payu_billing_state'));
        billingState = node('select');billingState.className = 'in';billingState.name = 'billing_state';billingState.required = true;
        const placeholder = node('option',tr('payu_select_state'));placeholder.value = '';billingState.append(placeholder);
        playChoice.states.forEach(state=>{const option=node('option',state);option.value=state;billingState.append(option);});
        stateLabel.append(billingState);form.append(stateLabel);
      }
      const fields={};
      [['name','text','name'],['email','email','email'],['phone','tel','tel-national']].forEach(([name,type,autocomplete])=>{
        const label=node('label',tr('payu_'+name)),input=node('input');input.className='in';input.name=name;input.type=type;input.autocomplete=autocomplete;input.required=true;input.maxLength=name==='name'?80:name==='email'?232:10;
        if(name==='phone'){input.pattern='[6-9][0-9]{9}';input.inputMode='numeric';}
        label.append(input);form.append(label);fields[name]=input;
      });
      const label=node('label'),consent=node('input');label.className='membership-consent';consent.type='checkbox';consent.required=true;consent.name='contact_consent';
      label.append(consent,node('span',tr('payu_contact_consent')));form.append(label);
      const error=node('p');error.setAttribute('role','status');form.append(error);
      const submit=node('button',tr('payu_continue'));submit.type='submit';submit.className='btn btn-primary';form.append(submit);
      form.addEventListener('submit',async event=>{
        event.preventDefault();if(submit.disabled || !current() || (!allowedCheckout() && !playChoice))return;
        if (playChoice && !(Date.parse(playChoice.expires_at) > Date.now())) {error.textContent=tr('payu_error');return;}
        submit.disabled=true;error.textContent='';
        try {
          const response=await fetch('/api/v1/payments/payu/orders',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan_id:plans.value,name:fields.name.value.trim(),email:fields.email.value.trim(),phone:fields.phone.value.trim(),contact_consent:consent.checked,...(playChoice?{play_choice_id:playChoice.choice_id,billing_state:billingState.value}:{})})});
          if(!response.ok)throw Error('checkout_unavailable');
          const order=await response.json();
          if (!current()) return;
          if(!['https://secure.payu.in/_payment','https://test.payu.in/_payment'].includes(order.action_url) || !order.fields || typeof order.fields!=='object')throw Error('invalid_checkout');
          const outbound=node('form');outbound.method='POST';outbound.action=order.action_url;outbound.hidden=true;
          const allowed=['key','txnid','amount','productinfo','firstname','email','phone','surl','furl','udf1','udf2','udf3','udf4','udf5','hash'];
          Object.keys(order.fields).forEach(name=>{if(!allowed.includes(name)||typeof order.fields[name]!=='string'||order.fields[name].length>2048)throw Error('invalid_checkout');const input=node('input');input.type='hidden';input.name=name;input.value=order.fields[name];outbound.append(input);});
          document.body.append(outbound);HTMLFormElement.prototype.submit.call(outbound);
        } catch (_) {error.textContent=tr('payu_error');submit.disabled=false;}
      });
      slot.append(form);
    } catch (_) { /* Existing no-payment notice remains truthful. */ }
  };
  async function refreshAccess(panel, button) {
    if (button) button.disabled=true;
    try {
      const response=await fetch('/api/v1/membership/status',{credentials:'same-origin',cache:'no-store'});
      if (!response.ok || !panel.isConnected) return;
      const value=await response.json();
      const words=JSON.parse(document.getElementById('ss-boot').textContent).t||{};
      const line=panel.querySelector('[data-membership-status]');
      if (line) line.textContent=words['membership_'+value.state]||value.state;
      const start=panel.querySelector('[data-membership-start]');
      if (start) start.hidden=value.state!=='available';
      if (window.SSMembershipRenew) await window.SSMembershipRenew();
    } catch (_) { /* Manual retry preserves existing account and study data. */ }
    finally {if(button)button.disabled=false;}
  }
  window.addEventListener('ss-payu-return',function(){
    if (!nativeApp() || !allowedCheckout()) return;
    const panel=document.querySelector('#membershipPanel');
    if(panel)refreshAccess(panel);
  });
  // Compatible WebViews can inject the immutable native policy after deferred
  // scripts. Re-read server status, never create an order or assume entitlement.
  window.addEventListener('ss-membership-ready', async function () {
    if (!allowedCheckout()) return;
    const panel = document.querySelector('#membershipPanel');
    if (!panel) return;
    try {
      const response = await fetch('/api/v1/membership/status', {credentials:'same-origin',cache:'no-store'});
      if (response.ok && panel.isConnected) window.SSMembershipCheckout(panel, await response.json());
    } catch (_) { /* A later visit can retry without changing local progress. */ }
  });
}());
