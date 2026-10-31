/* First-party, accessible confirmations. Data is inserted as text, never HTML. */
(function () {
  'use strict';
  var active = null, boot = document.getElementById('ss-boot');
  var strings = boot ? JSON.parse(boot.textContent).t : {};
  function node(tag, cls, text) {
    var el = document.createElement(tag); if (cls) el.className = cls;
    if (text != null) el.textContent = text; return el;
  }
  function confirm(options) {
    if (active) return Promise.resolve(false);
    return new Promise(function (resolve) {
      var previous = document.activeElement, settled = false;
      var dialog = node('dialog', 'ss-dialog');
      dialog.dataset.tone = options.danger ? 'danger' : 'normal';
      dialog.setAttribute('role', 'alertdialog');
      dialog.setAttribute('aria-labelledby', 'ss-dialog-title');
      dialog.setAttribute('aria-describedby', 'ss-dialog-message');
      var body = node('div', 'ss-dialog-body');
      var icon = node('span', 'ss-dialog-icon', options.danger ? '!' : '↧');
      icon.setAttribute('aria-hidden', 'true');
      var title = node('h2', '', options.title); title.id = 'ss-dialog-title';
      var message = node('p', '', options.message); message.id = 'ss-dialog-message';
      body.append(icon, title, message);
      if (options.context) body.appendChild(node('p', 'ss-dialog-context', options.context));
      var footer = node('div', 'ss-dialog-actions');
      var cancel = node('button', 'btn btn-secondary', strings.dialog_cancel);
      cancel.type = 'button'; cancel.autofocus = true; cancel.dataset.dialogCancel = '';
      var proceed = node('button', 'btn btn-primary', options.confirmLabel || strings.dialog_confirm);
      proceed.type = 'button'; proceed.dataset.dialogConfirm = '';
      footer.append(cancel, proceed); dialog.append(body, footer);
      function finish(accepted) {
        if (settled) return; settled = true; active = null;
        if (dialog.open) dialog.close(); dialog.remove();
        if (previous && previous.isConnected) previous.focus({preventScroll:true});
        resolve(accepted);
      }
      cancel.addEventListener('click', function () { finish(false); });
      proceed.addEventListener('click', function () { finish(true); });
      dialog.addEventListener('cancel', function (e) { e.preventDefault(); finish(false); });
      dialog.addEventListener('close', function () { finish(false); });
      active = function () { finish(false); };
      document.body.appendChild(dialog); dialog.showModal(); cancel.focus();
    });
  }
  ['hashchange', 'popstate', 'pagehide'].forEach(function (event) {
    window.addEventListener(event, function () { if (active) active(); });
  });
  window.SSDialog = { confirm: confirm, cancel: function () { if (active) active(); } };
})();
