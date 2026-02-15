import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { authService } from '../services/auth';

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const validatePassword = (pwd) => {
    if (pwd.length < 6) return 'Минимум 6 символов';
    if (pwd.length > 1000) return 'Пароль слишком длинный (максимум 1000 символов)';
    if (!/\d/.test(pwd)) return 'Нужна хотя бы одна цифра';
    if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(pwd)) return 'Нужен хотя бы один спецсимвол';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const pwdError = validatePassword(password);
    if (pwdError) {
      setError(pwdError);
      return;
    }
    
    setLoading(true);
    try {
      const res = await api.register(email, password, displayName);
      if (res.ok) {
        setSuccess(true);
        setError('');
        // Показываем плашку успеха 2 секунды, затем редирект
        setTimeout(() => {
          navigate('/login', { state: { message: 'Регистрация успешна! Войдите в систему.' } });
        }, 2000);
      } else {
        setError(res.data?.detail || 'Ошибка регистрации');
        setSuccess(false);
      }
    } catch (err) {
      setError('Ошибка подключения к серверу');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-pm-bg">
      <div className="bg-pm-bg-lighter p-8 rounded-lg shadow-lg w-full max-w-md border border-pm-border">
        <h1 className="text-2xl font-bold text-pm-text mb-6">Регистрация</h1>
        
        {success && (
          <div className="bg-green-500/20 border border-green-500 text-green-300 p-3 rounded mb-4 animate-pulse">
            ✅ Регистрация успешна! Перенаправление на страницу входа...
          </div>
        )}
        
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-pm-text-muted mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 bg-pm-bg border border-pm-border rounded text-pm-text"
              required
            />
          </div>
          
          <div>
            <label className="block text-pm-text-muted mb-2">Имя (необязательно)</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full p-3 bg-pm-bg border border-pm-border rounded text-pm-text"
            />
          </div>
          
          <div>
            <label className="block text-pm-text-muted mb-2">Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 bg-pm-bg border border-pm-border rounded text-pm-text"
              required
            />
            <p className="text-pm-text-muted text-sm mt-1">
              Минимум 6 символов, 1 цифра, 1 спецсимвол
            </p>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-pm-orange hover:bg-pm-orange-dark text-white p-3 rounded font-medium disabled:opacity-50"
          >
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>
        
        <p className="mt-6 text-center text-pm-text-muted">
          Уже есть аккаунт?{' '}
          <Link to="/login" className="text-pm-orange hover:underline">
            Войти
          </Link>
        </p>
      </div>
    </div>
  );
}
