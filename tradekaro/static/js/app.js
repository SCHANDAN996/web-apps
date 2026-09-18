/* ═══════════════════════════════════════════════════════════════
   TradeKaro AI — Core Application JavaScript
   Single SocketIO, Global State, Keyboard Shortcuts, Utilities
   ═══════════════════════════════════════════════════════════════ */

// ─── Command Registry for Command Palette ───
const CMD_REGISTRY = [
    { label: 'Dashboard', href: '/', icon: 'fa-solid fa-chart-pie', hint: 'Command Center' },
    { label: 'Terminal', href: '/terminal', icon: 'fa-solid fa-chart-line', hint: 'Market Charts' },
    { label: 'AI Brain', href: '/brain', icon: 'fa-solid fa-brain', hint: 'Neural Monitor' },
    { label: 'Trade Journal', href: '/journal', icon: 'fa-solid fa-book', hint: 'History' },
    { label: 'Options Lab', href: '/options', icon: 'fa-solid fa-layer-group', hint: 'Option Chain' },
    { label: 'Portfolio', href: '/portfolio', icon: 'fa-solid fa-wallet', hint: 'Risk & Analytics' },
    { label: 'Intelligence', href: '/news', icon: 'fa-solid fa-newspaper', hint: 'News & Heatmap' },
    { label: 'Settings', href: '/settings', icon: 'fa-solid fa-sliders', hint: 'Configuration' },
];

// ─── Smart Data Fetcher ───
async function smartFetch(url, fallback = null) {
    if (document.hidden) return fallback;
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(res.statusText);
        return await res.json();
    } catch (e) {
        console.warn(`Fetch failed: ${url}`, e.message);
        return fallback;
    }
}

// ─── Number Formatter ───
function formatNum(n) {
    if (n === null || n === undefined || isNaN(n)) return '0';
    return Number(n).toLocaleString('en-IN');
}

function formatCurrency(n) {
    if (n === null || n === undefined || isNaN(n)) return '₹0';
    return '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

// ─── Main App Shell ───
function appShell() {
    return {
        // Layout state
        sidebarOpen: window.innerWidth > 1279,
        mobileNav: false,
        aiPanelOpen: false,
        blotterOpen: false,
        blotterTab: 'positions',

        // Modals
        commandPalette: false,
        killModal: false,
        killConfirmText: '',

        // Global data
        globalPnl: 0,
        cpu: 0,
        connected: false,
        clock: '--:--:--',
        positions: [],
        systemLogs: [],
        aiLogs: [],

        // AI Chat
        aiMessages: [],
        aiInput: '',
        aiTyping: false,

        // Command Palette
        cmdQuery: '',
        cmdResults: [...CMD_REGISTRY],

        // Toasts
        toasts: [],
        toastId: 0,

        // Socket
        _socket: null,
        _logId: 0,

        init() {
            // Clock
            this.updateClock();
            setInterval(() => this.updateClock(), 1000);

            // Socket
            this.initSocket();

            // Data polling
            this.fetchGlobalData();
            setInterval(() => this.fetchGlobalData(), 5000);

            // Positions
            this.fetchPositions();
            setInterval(() => {
                if (!document.hidden) this.fetchPositions();
            }, 3000);

            // Watch command palette open to focus input
            this.$watch('commandPalette', (val) => {
                if (val) {
                    this.cmdQuery = '';
                    this.cmdResults = [...CMD_REGISTRY];
                    this.$nextTick(() => {
                        const inp = this.$refs.cmdInput;
                        if (inp) inp.focus();
                    });
                }
            });
        },

        // ─── Clock ───
        updateClock() {
            this.clock = new Date().toLocaleTimeString('en-IN', { hour12: false, timeZone: 'Asia/Kolkata' });
        },

        // ─── Socket Connection (Single!) ───
        initSocket() {
            try {
                this._socket = io({ reconnection: true, reconnectionDelay: 2000, reconnectionAttempts: 50 });

                this._socket.on('connect', () => {
                    this.connected = true;
                    console.log('🟢 Socket connected');
                });
                this._socket.on('disconnect', () => {
                    this.connected = false;
                    console.log('🔴 Socket disconnected');
                });

                // System logs
                this._socket.on('log_update', (data) => {
                    const t = new Date().toLocaleTimeString('en-IN', { hour12: false }).slice(0, 5);
                    this.systemLogs.unshift({ id: this._logId++, time: t, text: data.log.slice(0, 120) });
                    if (this.systemLogs.length > 150) this.systemLogs.pop();
                });

                // AI thoughts
                this._socket.on('ai_log_update', (data) => {
                    const t = new Date().toLocaleTimeString('en-IN', { hour12: false }).slice(0, 5);
                    this.aiLogs.unshift({ id: this._logId++, time: t, text: data.log.slice(0, 120) });
                    if (this.aiLogs.length > 150) this.aiLogs.pop();
                });

                // Brain updates
                this._socket.on('brain_update', (data) => {
                    // Dispatch custom event for brain page to catch
                    window.dispatchEvent(new CustomEvent('brain-update', { detail: data }));
                });

                // Trade updates
                this._socket.on('trade_update', (data) => {
                    this.positions.unshift(data);
                    if (this.positions.length > 50) this.positions.pop();
                    this.notify(`Trade: ${data.action === 'B' ? 'BUY' : 'SELL'} ${data.symbol}`, 'info');
                });
            } catch (e) {
                console.error('Socket init error:', e);
            }
        },

        // ─── Data Fetching ───
        async fetchGlobalData() {
            if (document.hidden) return;
            const [pnl, sys] = await Promise.all([
                smartFetch('/api/pnl', {}),
                smartFetch('/api/system-stats', {})
            ]);
            if (pnl && pnl.net_pnl !== undefined) this.globalPnl = Math.round(pnl.net_pnl);
            if (sys && sys.cpu !== undefined) this.cpu = sys.cpu;
        },

        async fetchPositions() {
            const data = await smartFetch('/api/trade-history', []);
            if (Array.isArray(data)) this.positions = data;
        },

        // ─── AI Chat ───
        async sendAiMessage() {
            const text = this.aiInput.trim();
            if (!text) return;

            this.aiMessages.push({ id: Date.now(), text, sender: 'user' });
            this.aiInput = '';
            this.aiTyping = true;
            this.scrollAiChat();

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                setTimeout(() => {
                    this.aiMessages.push({ id: Date.now() + 1, text: data.response, sender: 'ai' });
                    this.aiTyping = false;
                    this.scrollAiChat();
                }, 400);
            } catch (e) {
                this.aiTyping = false;
                this.aiMessages.push({ id: Date.now() + 1, text: 'Connection error. Try again.', sender: 'ai' });
                this.scrollAiChat();
            }
        },

        scrollAiChat() {
            this.$nextTick(() => {
                const el = document.getElementById('ai-chat-area');
                if (el) el.scrollTop = el.scrollHeight;
            });
        },

        // ─── Command Palette ───
        filterCommands() {
            const q = this.cmdQuery.toLowerCase();
            if (!q) { this.cmdResults = [...CMD_REGISTRY]; return; }
            this.cmdResults = CMD_REGISTRY.filter(c =>
                c.label.toLowerCase().includes(q) || (c.hint && c.hint.toLowerCase().includes(q))
            );
        },

        // ─── Keyboard Shortcuts ───
        handleKeydown(e) {
            // ⌘K or Ctrl+K — Command Palette
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                this.commandPalette = !this.commandPalette;
            }
            // ⌘B or Ctrl+B — AI Panel
            if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
                e.preventDefault();
                this.aiPanelOpen = !this.aiPanelOpen;
            }
            // Escape — close modals
            if (e.key === 'Escape') {
                this.commandPalette = false;
                this.killModal = false;
                this.killConfirmText = '';
            }
        },

        // ─── Kill Switch ───
        executeKill() {
            if (this.killConfirmText !== 'KILL') return;
            fetch('/api/kill_switch', { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    this.notify('⚠️ EMERGENCY STOP ACTIVATED!', 'error');
                    this.killModal = false;
                    this.killConfirmText = '';
                })
                .catch(() => this.notify('Kill switch failed!', 'error'));
        },

        // ─── Bot Control ───
        async controlBot(action) {
            try {
                const res = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });
                const data = await res.json();
                this.notify(data.message, action === 'start' ? 'success' : 'info');
            } catch (e) {
                this.notify('Bot control failed', 'error');
            }
        },

        // ─── Quick Trade ───
        async placeTrade(symbol, qty, side, type = 'MKT') {
            if (!symbol) { this.notify('Enter symbol', 'warning'); return; }
            try {
                const res = await fetch('/api/place_trade', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol: symbol.toUpperCase(), qty: parseInt(qty), side, type, price: 0 })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    this.notify(`${side === 'B' ? 'BUY' : 'SELL'} order sent for ${symbol}`, 'success');
                } else {
                    this.notify(data.message, 'error');
                }
            } catch (e) {
                this.notify('Trade failed', 'error');
            }
        },

        // ─── Toast Notifications ───
        notify(message, type = 'info') {
            const id = this.toastId++;
            this.toasts.push({ id, message, type, visible: true });
            setTimeout(() => this.removeToast(id), 5000);
        },

        removeToast(id) {
            const idx = this.toasts.findIndex(t => t.id === id);
            if (idx > -1) {
                this.toasts[idx].visible = false;
                setTimeout(() => {
                    this.toasts = this.toasts.filter(t => t.id !== id);
                }, 300);
            }
        },

        // ─── Utilities ───
        formatNum(n) { return formatNum(n); },
        formatCurrency(n) { return formatCurrency(n); }
    };
}
