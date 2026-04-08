import { useState } from 'react';
import { login } from '../api/apiClient';
import './AuthForm.css';

export default function LoginForm({ onLoginSuccess, onSwitchToRegister }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { token } = await login(email, password);
      onLoginSuccess(token);
    } catch (err) {
      setError(err.message || 'Login gagal. Periksa email dan password Anda.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card__header">
          <div className="auth-card__icon">✅</div>
          <h1 className="auth-card__title">Task Management</h1>
          <h2 className="auth-card__subtitle">Login — Masuk ke akun Anda</h2>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="auth-form__error" role="alert">
              <span className="auth-form__error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="auth-form__field">
            <label htmlFor="login-email" className="auth-form__label">Email</label>
            <input
              id="login-email"
              type="email"
              className="auth-form__input"
              placeholder="nama@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="auth-form__field">
            <label htmlFor="login-password" className="auth-form__label">Password</label>
            <input
              id="login-password"
              type="password"
              className="auth-form__input"
              placeholder="Minimal 8 karakter"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="auth-form__submit"
            disabled={submitting}
          >
            {submitting ? (
              <span className="auth-form__spinner">Masuk...</span>
            ) : (
              'Masuk'
            )}
          </button>
        </form>

        <p className="auth-card__switch">
          Belum punya akun?{' '}
          <button className="auth-card__switch-btn" onClick={onSwitchToRegister}>
            Daftar sekarang
          </button>
        </p>
      </div>
    </div>
  );
}
