/* Admin: confirm destructive buttons (no inline handlers — CSP). */
document.addEventListener('click', function (e) {
  var b = e.target.closest('[data-confirm]');
  if (b && !window.confirm(b.getAttribute('data-confirm'))) e.preventDefault();
});
/* Questions list: "select all" box for the bulk verify/hide form. */
document.addEventListener('change', function (e) {
  if (e.target.id !== 'bulkAll') return;
  document.querySelectorAll('#bulkForm input[name=ids]').forEach(function (c) { c.checked = e.target.checked; });
});
