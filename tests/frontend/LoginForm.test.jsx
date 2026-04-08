import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi } from 'vitest';
import LoginForm from '../../src/frontend/components/LoginForm';

vi.mock('../../src/frontend/api/apiClient', () => ({
  login: vi.fn(),
}));

import { login } from '../../src/frontend/api/apiClient';

describe('LoginForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('merender field email, password, dan tombol submit', () => {
    render(<LoginForm onLoginSuccess={vi.fn()} />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /masuk/i })).toBeInTheDocument();
  });

  it('submit sukses memanggil onLoginSuccess dengan token', async () => {
    login.mockResolvedValueOnce({ token: 'jwt-token-123' });
    const onLoginSuccess = vi.fn();
    render(<LoginForm onLoginSuccess={onLoginSuccess} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /masuk/i })); });

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith('user@example.com', 'password123');
      expect(onLoginSuccess).toHaveBeenCalledWith('jwt-token-123');
    });
  });

  it('menampilkan pesan error jika login gagal', async () => {
    login.mockRejectedValueOnce(new Error('Email atau password salah'));
    render(<LoginForm onLoginSuccess={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrongpass' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /masuk/i })); });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Email atau password salah');
    });
  });

  it('tombol disabled saat submitting', async () => {
    let resolve;
    login.mockReturnValueOnce(new Promise((r) => { resolve = r; }));
    render(<LoginForm onLoginSuccess={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /masuk/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /masuk/i })).toBeDisabled();
    });
    resolve({ token: 'tok' });
  });

  it('tidak menampilkan error saat pertama kali render', () => {
    render(<LoginForm onLoginSuccess={vi.fn()} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('merender tombol switch ke register jika prop onSwitchToRegister diberikan', () => {
    render(<LoginForm onLoginSuccess={vi.fn()} onSwitchToRegister={vi.fn()} />);
    expect(screen.getByRole('button', { name: /daftar/i })).toBeInTheDocument();
  });

  it('memanggil onSwitchToRegister saat tombol daftar diklik', () => {
    const onSwitch = vi.fn();
    render(<LoginForm onLoginSuccess={vi.fn()} onSwitchToRegister={onSwitch} />);
    fireEvent.click(screen.getByRole('button', { name: /daftar/i }));
    expect(onSwitch).toHaveBeenCalledTimes(1);
  });

  it('error sebelumnya hilang saat submit ulang berhasil', async () => {
    login.mockRejectedValueOnce(new Error('Gagal'));
    const onLoginSuccess = vi.fn();
    render(<LoginForm onLoginSuccess={onLoginSuccess} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /masuk/i })); });
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());

    login.mockResolvedValueOnce({ token: 'tok' });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /masuk/i })); });
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  });
});

// Feature: task-auth-deadline-calendar, Property 20: Form menampilkan pesan error saat operasi gagal
describe('LoginForm — Property 20', () => {
  beforeEach(() => vi.clearAllMocks());

  it('[PBT] Property 20: LoginForm menampilkan pesan error non-kosong saat login gagal', async () => {
    const { default: fc } = await import('fast-check');

    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1 }),
        async (errorMessage) => {
          login.mockRejectedValueOnce(new Error(errorMessage));
          const { unmount } = render(<LoginForm onLoginSuccess={vi.fn()} />);

          fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
          fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
          await act(async () => { fireEvent.click(screen.getByRole('button', { name: /masuk/i })); });

          await waitFor(() => {
            const alert = screen.getByRole('alert');
            expect(alert).toBeInTheDocument();
            expect(alert.textContent.length).toBeGreaterThan(0);
          });

          unmount();
          vi.clearAllMocks();
        }
      ),
      { numRuns: 10 }
    );
  });
});
