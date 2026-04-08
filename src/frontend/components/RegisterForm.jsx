import { useState } from 'react';
import { register } from '../api/apiClient';
import './AuthForm.css';

export default function RegisterForm({ onRegisterSuccess, onSwitchToLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password);
      onRegisterSuccess();
    } catch (err) {
      setError(err.message || 'Registrasi gagal. Coba lagi.');
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
          <p className="auth-card__subtitle">Buat akun baru</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="auth-form__error" role="alert">
              <span className="auth-form__error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="auth-form__field">
            <label htmlFor="reg-email" className="auth-form__label">Email</label>
            <input
              id="reg-email"
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
            <label htmlFor="reg-password" className="auth-form__label">Password</label>
            <input
              id="reg-password"
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
            {submitting ? 'Mendaftar...' : 'Daftar'}
          </button>
        </form>

        <p className="auth-card__switch">
          Sudah punya akun?{' '}
          <button className="auth-card__switch-btn" onClick={onSwitchToLogin}>
            Masuk
          </button>
        </p>
      </div>
    </div>
  );
}
