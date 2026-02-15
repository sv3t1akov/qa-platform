import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);
    
    try {
      const res = await api.forgotPassword(email);
      if (res.ok) {
        setSuccess(true);
      } else {
        setError(res.data?.detail || 'Ошибка запроса');
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
        <h1 className="text-2xl font-bold text-pm-text mb-6">Восстановление пароля</h1>
        
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {success ? (
          <div className="bg-green-500/20 border border-green-500 text-green-300 p-3 rounded mb-4">
            Если email существует, инструкции отправлены на почту.
          </div>
        ) : (
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
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-pm-orange hover:bg-pm-orange-dark text-white p-3 rounded font-medium disabled:opacity-50"
            >
              {loading ? 'Отправка...' : 'Отправить инструкции'}
            </button>
          </form>
        )}
        
        <div className="mt-6 text-center">
          <Link to="/login" className="text-pm-orange hover:underline">
            Вернуться к входу
          </Link>
        </div>
      </div>
    </div>
  );
}
