import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi } from 'vitest';
import RegisterForm from '../../src/frontend/components/RegisterForm';

vi.mock('../../src/frontend/api/apiClient', () => ({
  register: vi.fn(),
}));

import { register } from '../../src/frontend/api/apiClient';

describe('RegisterForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('merender field email, password, dan tombol submit', () => {
    render(<RegisterForm onRegisterSuccess={vi.fn()} />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /daftar/i })).toBeInTheDocument();
  });

  it('submit sukses memanggil onRegisterSuccess', async () => {
    register.mockResolvedValueOnce({ id: 1, email: 'user@example.com', created_at: '2024-01-01T00:00:00' });
    const onRegisterSuccess = vi.fn();
    render(<RegisterForm onRegisterSuccess={onRegisterSuccess} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /daftar/i })); });

    await waitFor(() => {
      expect(register).toHaveBeenCalledWith('user@example.com', 'password123');
      expect(onRegisterSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it('menampilkan pesan error jika registrasi gagal', async () => {
    register.mockRejectedValueOnce(new Error('Terjadi kesalahan'));
    render(<RegisterForm onRegisterSuccess={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /daftar/i })); });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Terjadi kesalahan');
    });
  });

  it('menampilkan pesan error 409 email sudah digunakan', async () => {
    register.mockRejectedValueOnce(new Error('Email sudah terdaftar'));
    render(<RegisterForm onRegisterSuccess={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'existing@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /daftar/i })); });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Email sudah terdaftar');
    });
  });

  it('tombol disabled saat submitting', async () => {
    let resolve;
    register.mockReturnValueOnce(new Promise((r) => { resolve = r; }));
    render(<RegisterForm onRegisterSuccess={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /daftar/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /mendaftar/i })).toBeDisabled();
    });
    resolve({ id: 1, email: 'user@example.com', created_at: '2024-01-01T00:00:00' });
  });

  it('tidak menampilkan error saat pertama kali render', () => {
    render(<RegisterForm onRegisterSuccess={vi.fn()} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('merender tombol switch ke login jika prop onSwitchToLogin diberikan', () => {
    render(<RegisterForm onRegisterSuccess={vi.fn()} onSwitchToLogin={vi.fn()} />);
    expect(screen.getByRole('button', { name: /masuk/i })).toBeInTheDocument();
  });

  it('memanggil onSwitchToLogin saat tombol masuk diklik', () => {
    const onSwitch = vi.fn();
    render(<RegisterForm onRegisterSuccess={vi.fn()} onSwitchToLogin={onSwitch} />);
    fireEvent.click(screen.getByRole('button', { name: /masuk/i }));
    expect(onSwitch).toHaveBeenCalledTimes(1);
  });
});

// Feature: task-auth-deadline-calendar, Property 20: Form menampilkan pesan error saat operasi gagal
describe('RegisterForm — Property 20', () => {
  beforeEach(() => vi.clearAllMocks());

  it('[PBT] Property 20: RegisterForm menampilkan pesan error non-kosong saat registrasi gagal', async () => {
    const { default: fc } = await import('fast-check');

    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1 }),
        async (errorMessage) => {
          register.mockRejectedValueOnce(new Error(errorMessage));
          const { unmount } = render(<RegisterForm onRegisterSuccess={vi.fn()} />);

          fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
          fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
          await act(async () => { fireEvent.click(screen.getByRole('button', { name: /daftar/i })); });

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
