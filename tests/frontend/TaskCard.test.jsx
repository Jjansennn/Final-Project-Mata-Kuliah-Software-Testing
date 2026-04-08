import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import * as fc from 'fast-check';
import { vi } from 'vitest';
import TaskCard from '../../src/frontend/components/TaskCard';

vi.mock('../../src/frontend/api/apiClient', () => ({
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}));

import { updateTask, deleteTask } from '../../src/frontend/api/apiClient';

const baseTask = {
  id: 1,
  title: 'Test Task',
  description: 'A description',
  status: 'pending',
  deadline: null,
  is_overdue: false,
  created_at: '2024-01-15T10:00:00',
};

describe('TaskCard', () => {
  beforeEach(() => vi.clearAllMocks());

  it('merender title, description, dan tanggal', () => {
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('A description')).toBeInTheDocument();
    expect(screen.getByText(/2024/)).toBeInTheDocument();
  });

  it('merender StatusBadge dengan status task', () => {
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  // --- Deadline display tests (Requirements 6.1, 6.2, 6.3) ---

  it('menampilkan deadline dalam format yang dapat dibaca jika deadline tidak null', () => {
    const task = { ...baseTask, deadline: '2024-08-01T17:00:00' };
    render(<TaskCard task={task} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    expect(screen.queryByText('2024-08-01T17:00:00')).not.toBeInTheDocument();
    const deadlineParagraph = screen.getByText(/deadline/i);
    expect(deadlineParagraph).toBeInTheDocument();
    expect(deadlineParagraph.textContent).toMatch(/2024/i);
  });

  it('menampilkan badge overdue jika is_overdue === true', () => {
    const task = { ...baseTask, deadline: '2024-01-01T00:00:00', is_overdue: true };
    render(<TaskCard task={task} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    const article = screen.getByRole('article');
    expect(article.className).toContain('task-card--overdue');
    expect(screen.getByText(/overdue/i)).toBeInTheDocument();
  });

  it('tidak menampilkan info deadline jika task.deadline null', () => {
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    expect(screen.queryByText(/deadline/i)).not.toBeInTheDocument();
  });

  it('tidak menampilkan class overdue jika is_overdue === false', () => {
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    const article = screen.getByRole('article');
    expect(article.className).not.toContain('task-card--overdue');
  });

  // --- Property 16: TaskCard menampilkan deadline yang dapat dibaca (Requirements 6.1) ---
  it('[PBT] Property 16: TaskCard menampilkan deadline yang dapat dibaca', () => {
    fc.assert(
      fc.property(
        fc.date({ min: new Date('2020-01-01'), max: new Date('2030-12-31') })
          .filter((d) => !isNaN(d.getTime())),
        (date) => {
          const isoString = date.toISOString();
          const task = { ...baseTask, deadline: isoString };
          const { unmount, container } = render(
            <TaskCard task={task} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />
          );
          const rawIsoPresent = container.textContent.includes(isoString);
          const deadlinePresent = container.textContent.toLowerCase().includes('deadline');
          unmount();
          return !rawIsoPresent && deadlinePresent;
        }
      ),
      { numRuns: 15 }
    );
  });

  // --- Property 17: TaskCard menampilkan indikator overdue (Requirements 6.2) ---
  it('[PBT] Property 17: TaskCard menampilkan indikator overdue', () => {
    fc.assert(
      fc.property(
        fc.date({ min: new Date('2020-01-01'), max: new Date('2030-12-31') })
          .filter((d) => !isNaN(d.getTime())),
        fc.boolean(),
        (date, isOverdue) => {
          const task = { ...baseTask, deadline: date.toISOString(), is_overdue: isOverdue };
          const { unmount, container } = render(
            <TaskCard task={task} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />
          );
          const article = container.querySelector('article');
          const hasOverdueClass = article.className.includes('task-card--overdue');
          unmount();
          return hasOverdueClass === isOverdue;
        }
      ),
      { numRuns: 15 }
    );
  });

  // --- Existing tests ---

  it('[PBT] Property F5: TaskCard merender dropdown dengan ketiga opsi status', () => {
    fc.assert(
      fc.property(fc.constantFrom('pending', 'in_progress', 'done'), (status) => {
        const { unmount } = render(
          <TaskCard task={{ ...baseTask, status }} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />
        );
        const options = Array.from(screen.getByRole('combobox').options).map((o) => o.value);
        const result = options.includes('pending') && options.includes('in_progress') && options.includes('done');
        unmount();
        return result;
      }),
      { numRuns: 10 }
    );
  });

  it('[PBT] Property F6: perubahan status memanggil updateTask dan StatusBadge diperbarui', async () => {
    const STATUS_LABEL = { pending: 'Pending', in_progress: 'In Progress', done: 'Done' };
    await fc.assert(
      fc.asyncProperty(
        fc.constantFrom('pending', 'in_progress', 'done'),
        fc.constantFrom('pending', 'in_progress', 'done'),
        async (initialStatus, newStatus) => {
          updateTask.mockResolvedValueOnce({ ...baseTask, status: newStatus });
          const Wrapper = () => {
            const [task, setTask] = React.useState({ ...baseTask, status: initialStatus });
            return <TaskCard task={task} onStatusUpdated={(t) => setTask(t)} onTaskDeleted={vi.fn()} />;
          };
          const { unmount } = render(<Wrapper />);
          await act(async () => { fireEvent.change(screen.getByRole('combobox'), { target: { value: newStatus } }); });
          await waitFor(() => { expect(updateTask).toHaveBeenCalledWith(baseTask.id, { status: newStatus }); });
          await waitFor(() => { expect(screen.getByText(STATUS_LABEL[newStatus])).toBeInTheDocument(); });
          unmount();
          vi.clearAllMocks();
          return true;
        }
      ),
      { numRuns: 10 }
    );
  });

  it('dropdown disabled saat updating', async () => {
    let resolveUpdate;
    updateTask.mockReturnValueOnce(new Promise((resolve) => { resolveUpdate = resolve; }));
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'done' } });
    await waitFor(() => { expect(screen.getByRole('combobox')).toBeDisabled(); });
    resolveUpdate({ ...baseTask, status: 'done' });
  });

  it('error updateTask menampilkan pesan error', async () => {
    updateTask.mockRejectedValueOnce(new Error('Gagal memperbarui'));
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    await act(async () => { fireEvent.change(screen.getByRole('combobox'), { target: { value: 'done' } }); });
    await waitFor(() => { expect(screen.getByRole('alert')).toHaveTextContent('Gagal memperbarui'); });
  });

  it('[PBT] Property F7: konfirmasi hapus memanggil deleteTask dan onTaskDeleted', async () => {
    await fc.assert(
      fc.asyncProperty(fc.integer({ min: 1, max: 1000 }), async (taskId) => {
        vi.spyOn(window, 'confirm').mockReturnValue(true);
        deleteTask.mockResolvedValueOnce(undefined);
        const onTaskDeleted = vi.fn();
        const { unmount } = render(
          <TaskCard task={{ ...baseTask, id: taskId }} onStatusUpdated={vi.fn()} onTaskDeleted={onTaskDeleted} />
        );
        await act(async () => { fireEvent.click(screen.getByRole('button', { name: /hapus/i })); });
        await waitFor(() => {
          expect(deleteTask).toHaveBeenCalledWith(taskId);
          expect(onTaskDeleted).toHaveBeenCalledWith(taskId);
        });
        unmount();
        vi.clearAllMocks();
        return true;
      }),
      { numRuns: 10 }
    );
  });

  it('menampilkan pesan error jika deleteTask gagal', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    deleteTask.mockRejectedValueOnce(new Error('Gagal menghapus'));
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /hapus/i })); });
    await waitFor(() => { expect(screen.getByRole('alert')).toHaveTextContent('Gagal menghapus'); });
  });

  it('batalkan konfirmasi hapus tidak memanggil deleteTask', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(<TaskCard task={baseTask} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />);
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /hapus/i })); });
    expect(deleteTask).not.toHaveBeenCalled();
  });
});
