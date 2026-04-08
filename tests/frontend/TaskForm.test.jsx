import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import * as fc from 'fast-check';
import { vi } from 'vitest';
import TaskForm from '../../src/frontend/components/TaskForm';

vi.mock('../../src/frontend/api/apiClient', () => ({
  createTask: vi.fn(),
}));

import { createTask } from '../../src/frontend/api/apiClient';

describe('TaskForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('[PBT] Property F3: title valid → createTask dipanggil, form dikosongkan', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1 }).filter((s) => s.trim().length > 0),
        async (validTitle) => {
          createTask.mockResolvedValueOnce({ id: 1, title: validTitle, description: '', status: 'pending' });
          const { unmount } = render(<TaskForm onTaskCreated={vi.fn()} />);
          const titleInput = screen.getByLabelText('Title');
          fireEvent.change(titleInput, { target: { value: validTitle } });
          await act(async () => { fireEvent.click(screen.getByRole('button', { name: /tambah task/i })); });
          await waitFor(() => { expect(createTask).toHaveBeenCalledWith(validTitle, undefined, null); });
          expect(titleInput.value).toBe('');
          unmount();
          vi.clearAllMocks();
        }
      ),
      { numRuns: 10 }
    );
  });

  it('tombol submit disabled saat submitting === true', async () => {
    let resolveCreate;
    createTask.mockReturnValueOnce(new Promise((resolve) => { resolveCreate = resolve; }));
    render(<TaskForm onTaskCreated={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Test Task' } });
    fireEvent.click(screen.getByRole('button', { name: /tambah task/i }));
    await waitFor(() => { expect(screen.getByRole('button', { name: /menyimpan/i })).toBeDisabled(); });
    resolveCreate({ id: 1, title: 'Test Task', status: 'pending' });
  });

  it('merender field title dan description', () => {
    render(<TaskForm onTaskCreated={vi.fn()} />);
    expect(screen.getByLabelText('Title')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
  });

  it('menampilkan pesan error jika createTask gagal', async () => {
    createTask.mockRejectedValueOnce(new Error('Gagal menyimpan task'));
    render(<TaskForm onTaskCreated={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Test Task' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /tambah task/i })); });
    await waitFor(() => { expect(screen.getByRole('alert')).toHaveTextContent('Gagal menyimpan task'); });
  });

  it('[PBT] Property F4: title whitespace tidak memanggil createTask', () => {
    fc.assert(
      fc.property(
        fc.array(fc.constantFrom(' ', '\t', '\n'), { minLength: 1 }).map((chars) => chars.join('')),
        (whitespaceTitle) => {
          const { unmount } = render(<TaskForm onTaskCreated={vi.fn()} />);
          fireEvent.change(screen.getByLabelText('Title'), { target: { value: whitespaceTitle } });
          fireEvent.click(screen.getByRole('button', { name: /tambah task/i }));
          const result = createTask.mock.calls.length === 0;
          unmount();
          vi.clearAllMocks();
          return result;
        }
      ),
      { numRuns: 20 }
    );
  });

  // --- Deadline input tests (Requirements 6.4) ---

  it('merender input deadline bertipe datetime-local', () => {
    render(<TaskForm onTaskCreated={vi.fn()} />);
    const deadlineInput = screen.getByLabelText(/deadline/i);
    expect(deadlineInput).toBeInTheDocument();
    expect(deadlineInput.type).toBe('datetime-local');
  });

  it('submit tanpa deadline mengirim deadline: null ke createTask', async () => {
    createTask.mockResolvedValueOnce({ id: 1, title: 'Task', status: 'pending', deadline: null });
    render(<TaskForm onTaskCreated={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Task' } });
    // deadline input left empty
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /tambah task/i })); });
    await waitFor(() => {
      expect(createTask).toHaveBeenCalledWith('Task', undefined, null);
    });
  });

  it('submit dengan deadline mengirim ISO 8601 ke createTask', async () => {
    createTask.mockResolvedValueOnce({ id: 1, title: 'Task', status: 'pending', deadline: '2025-06-15T09:00:00.000Z' });
    render(<TaskForm onTaskCreated={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Task' } });
    fireEvent.change(screen.getByLabelText(/deadline/i), { target: { value: '2025-06-15T09:00' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /tambah task/i })); });
    await waitFor(() => {
      const [, , deadlineArg] = createTask.mock.calls[0];
      // Should be a valid ISO 8601 string
      expect(() => new Date(deadlineArg).toISOString()).not.toThrow();
      expect(deadlineArg).not.toBeNull();
    });
  });

  it('deadline input dikosongkan setelah submit sukses', async () => {
    createTask.mockResolvedValueOnce({ id: 1, title: 'Task', status: 'pending', deadline: null });
    render(<TaskForm onTaskCreated={vi.fn()} />);
    const deadlineInput = screen.getByLabelText(/deadline/i);
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Task' } });
    fireEvent.change(deadlineInput, { target: { value: '2025-06-15T09:00' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /tambah task/i })); });
    await waitFor(() => { expect(deadlineInput.value).toBe(''); });
  });
});
