import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import * as fc from 'fast-check';
import App from '../../src/frontend/App';
import { UnauthorizedError } from '../../src/frontend/api/apiClient';

vi.mock('../../src/frontend/api/apiClient', () => ({
  fetchTasks: vi.fn(),
  UnauthorizedError: class UnauthorizedError extends Error {
    constructor(message = 'Unauthorized') {
      super(message);
      this.name = 'UnauthorizedError';
    }
  },
  login: vi.fn(),
  register: vi.fn(),
}));

// Mock CalendarView to avoid lazy import issues in tests
vi.mock('../../src/frontend/components/CalendarView.jsx', () => ({
  default: ({ tasks }) => <div data-testid="calendar-view">CalendarView ({tasks.length} tasks)</div>,
}));

import { fetchTasks } from '../../src/frontend/api/apiClient';

const fakeTasks = [
  { id: 1, title: 'Task Pertama', description: '', status: 'pending', deadline: null, is_overdue: false, created_at: '', updated_at: '' },
  { id: 2, title: 'Task Kedua', description: '', status: 'done', deadline: null, is_overdue: false, created_at: '', updated_at: '' },
];

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  // --- 12.2 Unit Tests ---

  it('menampilkan LoginForm jika tidak ada token di localStorage', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
  });

  it('menampilkan halaman utama task setelah login sukses', async () => {
    fetchTasks.mockResolvedValueOnce(fakeTasks);
    localStorage.setItem('token', 'valid-token');
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /task management/i })).toBeInTheDocument();
    });
    expect(localStorage.getItem('token')).toBe('valid-token');
  });

  it('menyimpan token ke localStorage setelah login sukses via LoginForm', async () => {
    fetchTasks.mockResolvedValueOnce([]);
    render(<App />);

    // Simulate login success by triggering onLoginSuccess
    // LoginForm calls onLoginSuccess(token) when login succeeds
    // We need to mock the login API call inside LoginForm
    const { login } = await import('../../src/frontend/api/apiClient');
    login.mockResolvedValueOnce({ token: 'new-token' });

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /masuk/i });

    fireEvent.change(emailInput, { target: { value: 'user@test.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('new-token');
    });
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /task management/i })).toBeInTheDocument();
    });
  });

  it('logout menghapus token dari localStorage dan menampilkan LoginForm', async () => {
    fetchTasks.mockResolvedValueOnce(fakeTasks);
    localStorage.setItem('token', 'valid-token');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /logout/i }));

    expect(localStorage.getItem('token')).toBeNull();
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
  });

  it('auto-logout saat API mengembalikan 401 (UnauthorizedError)', async () => {
    localStorage.setItem('token', 'expired-token');
    fetchTasks.mockRejectedValueOnce(new UnauthorizedError('Token tidak valid'));
    render(<App />);

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBeNull();
    });
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
  });

  it('toggle view antara list dan kalender', async () => {
    fetchTasks.mockResolvedValueOnce(fakeTasks);
    localStorage.setItem('token', 'valid-token');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /kalender/i })).toBeInTheDocument();
    });

    // Default is list view
    expect(screen.getByRole('heading', { name: /tambah task baru/i })).toBeInTheDocument();

    // Switch to calendar
    fireEvent.click(screen.getByRole('button', { name: /kalender/i }));
    await waitFor(() => {
      expect(screen.getByTestId('calendar-view')).toBeInTheDocument();
    });

    // Switch back to list
    fireEvent.click(screen.getByRole('button', { name: /list/i }));
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /tambah task baru/i })).toBeInTheDocument();
    });
  });

  it('meneruskan tasks ke CalendarView saat view === calendar', async () => {
    fetchTasks.mockResolvedValueOnce(fakeTasks);
    localStorage.setItem('token', 'valid-token');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /kalender/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /kalender/i }));

    await waitFor(() => {
      expect(screen.getByTestId('calendar-view')).toHaveTextContent(`${fakeTasks.length} tasks`);
    });
  });

  it('menampilkan "Memuat task..." saat fetchTasks belum selesai', () => {
    localStorage.setItem('token', 'valid-token');
    fetchTasks.mockReturnValue(new Promise(() => {}));
    render(<App />);
    expect(screen.getByText('Memuat task...')).toBeInTheDocument();
  });

  it('menampilkan error banner jika fetchTasks gagal dengan error non-401', async () => {
    localStorage.setItem('token', 'valid-token');
    fetchTasks.mockRejectedValueOnce(new Error('Gagal memuat data'));
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
    expect(screen.getByRole('alert')).toHaveTextContent('Gagal memuat data');
    expect(screen.getByRole('button', { name: /coba lagi/i })).toBeInTheDocument();
  });

  // --- 12.3 Property Tests ---

  /**
   * Property 18: Logout menghapus token dan menampilkan login
   * Validates: Requirements 7.3
   */
  it('Property 18: untuk semua token valid, logout selalu menghapus token dan menampilkan LoginForm', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
        async (token) => {
          vi.clearAllMocks();
          localStorage.clear();
          fetchTasks.mockResolvedValue([]);
          localStorage.setItem('token', token);

          const { unmount } = render(<App />);

          await waitFor(() => {
            expect(screen.queryByRole('button', { name: /logout/i })).toBeInTheDocument();
          });

          fireEvent.click(screen.getByRole('button', { name: /logout/i }));

          // Token must be removed from localStorage
          expect(localStorage.getItem('token')).toBeNull();
          // LoginForm must be displayed
          expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Property 19: Auto-logout saat API mengembalikan 401
   * Validates: Requirements 7.4
   */
  it('Property 19: untuk semua token valid, jika API mengembalikan 401, App menghapus token dan menampilkan LoginForm', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
        async (token) => {
          vi.clearAllMocks();
          localStorage.clear();
          localStorage.setItem('token', token);
          fetchTasks.mockRejectedValue(new UnauthorizedError('Token tidak valid'));

          const { unmount } = render(<App />);

          await waitFor(() => {
            expect(localStorage.getItem('token')).toBeNull();
          });

          // LoginForm must be displayed
          expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 10 }
    );
  });
});
