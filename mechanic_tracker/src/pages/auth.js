/**
 * Auth page — Login / Signup (demo mode: auto-skip)
 */
import { supabase, isSupabaseReady } from '../lib/supabase.js';

export function renderAuth(container, onAuth) {
  // If Supabase not configured, skip auth (demo mode)
  if (!isSupabaseReady()) {
    onAuth({ id: 'demo-user', email: 'demo@mechanic.app' });
    return;
  }

  let isLogin = true;

  function render() {
    container.innerHTML = `
      <div class="auth-container">
        <div class="auth-logo">🔧</div>
        <h1 class="auth-title">Core Return Tracker</h1>
        <p class="auth-subtitle">Track your core deposits. Recover every refund.</p>
        <form class="auth-form" id="auth-form">
          <div class="form-group">
            <label class="form-label">Email</label>
            <input type="email" class="form-input" id="auth-email" placeholder="you@shop.com" required autocomplete="email" />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" class="form-input" id="auth-password" placeholder="••••••••" required minlength="6" autocomplete="current-password" />
          </div>
          <div id="auth-error" class="form-error" style="margin-bottom:12px;"></div>
          <button type="submit" class="btn btn-primary btn-block" id="auth-submit">
            ${isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>
        <div class="auth-toggle">
          ${isLogin
            ? 'New here? <a id="auth-toggle-link">Create an account</a>'
            : 'Already have an account? <a id="auth-toggle-link">Sign in</a>'}
        </div>
        <button class="btn btn-ghost" id="auth-demo-btn" style="margin-top:24px; font-size:13px;">
          🎮 Try Demo Mode (No Account)
        </button>
      </div>
    `;

    document.getElementById('auth-toggle-link').addEventListener('click', () => {
      isLogin = !isLogin;
      render();
    });

    document.getElementById('auth-demo-btn').addEventListener('click', () => {
      onAuth({ id: 'demo-user', email: 'demo@mechanic.app' });
    });

    document.getElementById('auth-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('auth-email').value;
      const password = document.getElementById('auth-password').value;
      const errorEl = document.getElementById('auth-error');
      const btn = document.getElementById('auth-submit');

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>';
      errorEl.textContent = '';

      try {
        let result;
        if (isLogin) {
          result = await supabase.auth.signInWithPassword({ email, password });
        } else {
          result = await supabase.auth.signUp({ email, password });
        }
        if (result.error) throw result.error;
        onAuth(result.data.user);
      } catch (err) {
        errorEl.textContent = err.message || 'Authentication failed';
        btn.disabled = false;
        btn.textContent = isLogin ? 'Sign In' : 'Create Account';
      }
    });
  }

  render();
}
