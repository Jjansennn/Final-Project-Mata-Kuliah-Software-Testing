import { useState, useEffect, useCallback } from 'react';
import { fetchTasks, UnauthorizedError } from './api/apiClient';
import TaskForm from './components/TaskForm';
import TaskList from './components/TaskList';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import CalendarView from './components/CalendarView';
import './App.css';

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [authView, setAuthView] = useState('login'); // 'login' | 'register'
  const [view, setView] = useState('list'); // 'list' | 'calendar'
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadTasks = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchTasks()
      .then((data) => setTasks(data))
      .catch((err) => {
        if (err instanceof UnauthorizedError) {
          localStorage.removeItem('token');
          setToken(null);
        } else {
          setError(err.message);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (token) loadTasks();
  }, [token, loadTasks]);

  function handleLoginSuccess(newToken) {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  }

  function handleRegisterSuccess() {
    setAuthView('login');
  }

  function handleLogout() {
    localStorage.removeItem('token');
    setToken(null);
    setTasks([]);
  }

  function handleTaskCreated(newTask) {
    setTasks((prev) => [newTask, ...prev]);
  }

  function handleStatusUpdated(updatedTask) {
    setTasks((prev) => prev.map((t) => (t.id === updatedTask.id ? updatedTask : t)));
  }

  function handleTaskDeleted(taskId) {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  }

  // Auth screens
  if (!token) {
    if (authView === 'register') {
      return (
        <RegisterForm
          onRegisterSuccess={handleRegisterSuccess}
          onSwitchToLogin={() => setAuthView('login')}
        />
      );
    }
    return (
      <LoginForm
        onLoginSuccess={handleLoginSuccess}
        onSwitchToRegister={() => setAuthView('register')}
      />
    );
  }

  // Main app
  return (
    <>
      <header className="app-header">
        <div className="app-header__inner">
          <div className="app-header__brand">
            <span className="app-header__icon">✅</span>
            <h1 className="app-header__title">Task Management</h1>
          </div>
          <div className="app-header__actions">
            <button
              className={`app-header__view-btn${view === 'list' ? ' active' : ''}`}
              onClick={() => setView('list')}
              aria-label="List"
            >
              List
            </button>
            <button
              className={`app-header__view-btn${view === 'calendar' ? ' active' : ''}`}
              onClick={() => setView('calendar')}
              aria-label="Kalender"
            >
              Kalender
            </button>
            <button className="app-header__logout" onClick={handleLogout} aria-label="Logout">
              Keluar
            </button>
          </div>
        </div>
      </header>

      <main className="app-main">
        {loading ? (
          <div className="app-loading">
            <div className="app-loading__spinner" />
            <p>Memuat task...</p>
          </div>
        ) : error ? (
          <div className="app-error" role="alert">
            <p className="app-error__message">⚠️ {error}</p>
            <button className="app-error__retry" onClick={loadTasks}>
              Coba Lagi
            </button>
          </div>
        ) : (
          <>
            {view === 'list' ? (
              <>
                <TaskForm onTaskCreated={handleTaskCreated} />
                <TaskList
                  tasks={tasks}
                  onStatusUpdated={handleStatusUpdated}
                  onTaskDeleted={handleTaskDeleted}
                />
              </>
            ) : (
              <CalendarView
                tasks={tasks}
                onTaskClick={() => {}}
              />
            )}
          </>
        )}
      </main>
    </>
  );
}
