import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import api from '../services/api';

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('Токен сброса пароля отсутствует');
    }
  }, [token]);

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
    
    if (!token) {
      setError('Токен сброса пароля отсутствует');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }
    
    const pwdError = validatePassword(password);
    if (pwdError) {
      setError(pwdError);
      return;
    }
    
    setLoading(true);
    try {
      const res = await api.resetPassword(token, password);
      if (res.ok) {
        navigate('/login', { state: { message: 'Пароль успешно изменён! Войдите в систему.' } });
      } else {
        setError(res.data?.detail || 'Ошибка сброса пароля');
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
        <h1 className="text-2xl font-bold text-pm-text mb-6">Сброс пароля</h1>
        
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-pm-text-muted mb-2">Новый пароль</label>
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
          
          <div>
            <label className="block text-pm-text-muted mb-2">Подтвердите пароль</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full p-3 bg-pm-bg border border-pm-border rounded text-pm-text"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading || !token}
            className="w-full bg-pm-orange hover:bg-pm-orange-dark text-white p-3 rounded font-medium disabled:opacity-50"
          >
            {loading ? 'Сброс...' : 'Сбросить пароль'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <Link to="/login" className="text-pm-orange hover:underline">
            Вернуться к входу
          </Link>
        </div>
      </div>
    </div>
  );
}
