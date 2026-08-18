/**
 * Bottom navigation bar component
 */

// Lucide-style SVG icons (inline for zero-dependency)
const icons = {
  dashboard: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="4" rx="1"/><rect x="14" y="10" width="7" height="11" rx="1"/><rect x="3" y="13" width="7" height="8" rx="1"/></svg>`,
  add: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  tracker: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 14l2 2 4-4"/></svg>`,
  settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`,
};

export function renderNav(activeRoute) {
  const nav = document.getElementById('bottom-nav');
  if (!nav) return;

  const tabs = [
    { id: 'dashboard', icon: icons.dashboard, label: 'Home', route: '/' },
    { id: 'add', icon: icons.add, label: 'Add', route: '/add', isAdd: true },
    { id: 'tracker', icon: icons.tracker, label: 'Tracker', route: '/tracker' },
    { id: 'settings', icon: icons.settings, label: 'Settings', route: '/settings' },
  ];

  nav.innerHTML = tabs.map(tab => {
    const isActive = tab.route === activeRoute;
    const cls = `nav-item${isActive ? ' active' : ''}${tab.isAdd ? ' nav-add' : ''}`;
    return `<a class="${cls}" href="#${tab.route}" data-route="${tab.route}" id="nav-${tab.id}">
      ${tab.icon}
      <span>${tab.label}</span>
    </a>`;
  }).join('');

  nav.classList.remove('hidden');
}

export function hideNav() {
  const nav = document.getElementById('bottom-nav');
  if (nav) nav.classList.add('hidden');
}
