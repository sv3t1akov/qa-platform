import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import api from '../services/api';
import { authService } from '../services/auth';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Показываем сообщение об успешной регистрации, если оно передано через state
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Очищаем state, чтобы сообщение не показывалось при повторном переходе
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const res = await api.login(email, password);
      if (res.ok && res.data) {
        authService.setTokens(res.data.access_token, res.data.refresh_token);
        navigate('/', { replace: true });
      } else {
        setError(res.data?.detail || 'Ошибка входа');
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
        <h1 className="text-2xl font-bold text-pm-text mb-6">Вход</h1>
        
        {successMessage && (
          <div className="bg-green-500/20 border border-green-500 text-green-300 p-3 rounded mb-4">
            ✅ {successMessage}
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
            <label className="block text-pm-text-muted mb-2">Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 bg-pm-bg border border-pm-border rounded text-pm-text"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-pm-orange hover:bg-pm-orange-dark text-white p-3 rounded font-medium disabled:opacity-50"
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
        
        <div className="mt-6 flex justify-between text-sm">
          <Link to="/forgot-password" className="text-pm-orange hover:underline">
            Забыли пароль?
          </Link>
          <span className="text-pm-text-muted">
            Нет аккаунта?{' '}
            <Link to="/register" className="text-pm-orange hover:underline">
              Зарегистрироваться
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}
