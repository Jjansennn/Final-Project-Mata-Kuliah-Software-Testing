import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import * as fc from 'fast-check';
import { vi } from 'vitest';
import CalendarView from '../../src/frontend/components/CalendarView';

// Helper: build a task with a deadline on a specific date
function makeTask(id, day, month, year, overrides = {}) {
  const deadline = new Date(year, month, day, 12, 0, 0).toISOString();
  return {
    id,
    title: `Task ${id}`,
    description: '',
    status: 'pending',
    deadline,
    is_overdue: false,
    created_at: '',
    updated_at: '',
    ...overrides,
  };
}

// Helper: get days in a month
function daysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

// Fixed reference month: July 2024 (month index 6)
const YEAR = 2024;
const MONTH = 6; // July

describe('CalendarView', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 6, 15, 12, 0, 0));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // -----------------------------------------------------------------------
  // 14.2 Unit Tests
  // -----------------------------------------------------------------------

  it('merender header hari (Min–Sab)', () => {
    render(<CalendarView tasks={[]} onTaskClick={vi.fn()} />);
    ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'].forEach((h) => {
      expect(screen.getByText(h)).toBeInTheDocument();
    });
  });

  it('merender jumlah sel hari yang benar untuk bulan tertentu', () => {
    // July 2024 has 31 days — frozen time is 15 July 2024
    render(<CalendarView tasks={[]} onTaskClick={vi.fn()} />);
    // Frozen time: July 2024 (YEAR=2024, MONTH=6)
    const currentDays = daysInMonth(YEAR, MONTH);
    const dayCells = document.querySelectorAll('[data-day]');
    expect(dayCells.length).toBe(currentDays);
  });

  it('task muncul di sel tanggal yang sesuai deadline', () => {
    const task = makeTask(1, 15, MONTH, YEAR);
    render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);
    expect(screen.getByText('Task 1')).toBeInTheDocument();
  });

  it('task tanpa deadline tidak muncul di grid', () => {
    const taskNoDeadline = {
      id: 99,
      title: 'No Deadline Task',
      description: '',
      status: 'pending',
      deadline: null,
      is_overdue: false,
      created_at: '',
      updated_at: '',
    };
    render(<CalendarView tasks={[taskNoDeadline]} onTaskClick={vi.fn()} />);
    expect(screen.queryByText('No Deadline Task')).not.toBeInTheDocument();
  });

  it('navigasi bulan berikutnya memperbarui label bulan', () => {
    render(<CalendarView tasks={[]} onTaskClick={vi.fn()} />);
    const nextMonthDate = new Date(YEAR, MONTH + 1, 1);
    const expectedLabel = nextMonthDate.toLocaleString('id-ID', { month: 'long', year: 'numeric' });

    fireEvent.click(screen.getByRole('button', { name: /bulan berikutnya/i }));
    expect(screen.getByText(expectedLabel)).toBeInTheDocument();
  });

  it('navigasi bulan sebelumnya memperbarui label bulan', () => {
    render(<CalendarView tasks={[]} onTaskClick={vi.fn()} />);
    const prevMonthDate = new Date(YEAR, MONTH - 1, 1);
    const expectedLabel = prevMonthDate.toLocaleString('id-ID', { month: 'long', year: 'numeric' });

    fireEvent.click(screen.getByRole('button', { name: /bulan sebelumnya/i }));
    expect(screen.getByText(expectedLabel)).toBeInTheDocument();
  });

  it('klik task memanggil onTaskClick dengan task yang benar', () => {
    const task = makeTask(42, 15, MONTH, YEAR);
    const onTaskClick = vi.fn();
    render(<CalendarView tasks={[task]} onTaskClick={onTaskClick} />);

    fireEvent.click(screen.getByText('Task 42'));
    expect(onTaskClick).toHaveBeenCalledWith(task);
  });

  it('chip overdue memiliki class calendar-task--overdue', () => {
    const task = makeTask(5, 15, MONTH, YEAR, {
      is_overdue: true,
    });
    render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);
    const chip = screen.getByText('Task 5');
    expect(chip.className).toContain('calendar-task--overdue');
  });

  it('chip non-overdue tidak memiliki class calendar-task--overdue', () => {
    const task = makeTask(6, 15, MONTH, YEAR, {
      is_overdue: false,
    });
    render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);
    const chip = screen.getByText('Task 6');
    expect(chip.className).not.toContain('calendar-task--overdue');
  });

  it('filter status hanya menampilkan task yang sesuai', () => {
    const pendingTask = makeTask(10, 15, MONTH, YEAR, { status: 'pending' });
    const doneTask = makeTask(11, 15, MONTH, YEAR, { status: 'done' });

    render(<CalendarView tasks={[pendingTask, doneTask]} onTaskClick={vi.fn()} />);

    // Default: semua — both visible
    expect(screen.getByText('Task 10')).toBeInTheDocument();
    expect(screen.getByText('Task 11')).toBeInTheDocument();

    // Filter to pending only
    fireEvent.change(screen.getByRole('combobox', { name: /filter status/i }), {
      target: { value: 'pending' },
    });
    expect(screen.getByText('Task 10')).toBeInTheDocument();
    expect(screen.queryByText('Task 11')).not.toBeInTheDocument();

    // Filter to done only
    fireEvent.change(screen.getByRole('combobox', { name: /filter status/i }), {
      target: { value: 'done' },
    });
    expect(screen.queryByText('Task 10')).not.toBeInTheDocument();
    expect(screen.getByText('Task 11')).toBeInTheDocument();
  });

  it('filter in_progress hanya menampilkan task in_progress', () => {
    const inProgressTask = makeTask(20, 15, MONTH, YEAR, {
      status: 'in_progress',
    });
    const pendingTask = makeTask(21, 15, MONTH, YEAR, {
      status: 'pending',
    });

    render(<CalendarView tasks={[inProgressTask, pendingTask]} onTaskClick={vi.fn()} />);

    fireEvent.change(screen.getByRole('combobox', { name: /filter status/i }), {
      target: { value: 'in_progress' },
    });
    expect(screen.getByText('Task 20')).toBeInTheDocument();
    expect(screen.queryByText('Task 21')).not.toBeInTheDocument();
  });

  it('task di bulan berbeda tidak muncul di bulan saat ini', () => {
    // Task in next month (August 2024)
    const nextMonth = new Date(YEAR, MONTH + 1, 1);
    const task = makeTask(30, 1, nextMonth.getMonth(), nextMonth.getFullYear());
    render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);
    expect(screen.queryByText('Task 30')).not.toBeInTheDocument();
  });

  it('merender dropdown filter dengan semua opsi status', () => {
    render(<CalendarView tasks={[]} onTaskClick={vi.fn()} />);
    const select = screen.getByRole('combobox', { name: /filter status/i });
    const options = Array.from(select.options).map((o) => o.value);
    expect(options).toContain('semua');
    expect(options).toContain('pending');
    expect(options).toContain('in_progress');
    expect(options).toContain('done');
  });

  // -----------------------------------------------------------------------
  // 3.4 Fix-Check Test — Property 3: CalendarView deterministik dengan frozen time
  // Validates: Requirements 2.4
  // -----------------------------------------------------------------------

  it('[fix-check] task dengan deadline 15 Juli 2024 selalu muncul di sel hari ke-15 dengan frozen time', () => {
    // System time is frozen to 15 July 2024 12:00:00 via beforeEach
    const task = makeTask(100, 15, 6, 2024); // deadline: 15 Juli 2024
    render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);

    // Task must appear in the calendar
    expect(screen.getByText('Task 100')).toBeInTheDocument();

    // Task must appear specifically in the day-15 cell
    const cell = document.querySelector('[data-day="15"]');
    expect(cell).not.toBeNull();
    expect(cell.textContent).toContain('Task 100');
  });

  // -----------------------------------------------------------------------
  // 14.3 Property Tests
  // -----------------------------------------------------------------------

  /**
   * Property 21: CalendarView menampilkan jumlah sel yang benar
   * Validates: Requirements 8.2
   */
  it('[PBT] Property 21: CalendarView menampilkan jumlah sel yang benar untuk setiap bulan', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2020, max: 2030 }),
        fc.integer({ min: 0, max: 11 }),
        (year, month) => {
          const expectedDays = daysInMonth(year, month);
          // Render with a fixed initial month by navigating
          // We render and navigate to the target month
          const frozenDate = new Date(YEAR, MONTH, 15, 12, 0, 0);
          const { unmount } = render(<CalendarView tasks={[]} onTaskClick={vi.fn()} />);

          // Navigate to target year/month
          const currentYear = frozenDate.getFullYear();
          const currentMonth = frozenDate.getMonth();
          const monthDiff = (year - currentYear) * 12 + (month - currentMonth);

          const navBtn = monthDiff >= 0
            ? screen.getByRole('button', { name: /bulan berikutnya/i })
            : screen.getByRole('button', { name: /bulan sebelumnya/i });

          for (let i = 0; i < Math.abs(monthDiff); i++) {
            fireEvent.click(navBtn);
          }

          const dayCells = document.querySelectorAll('[data-day]');
          const result = dayCells.length === expectedDays;
          unmount();
          return result;
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Property 22: Task muncul di sel tanggal yang sesuai deadline
   * Validates: Requirements 8.3
   */
  it('[PBT] Property 22: task muncul di sel tanggal yang sesuai deadline', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 28 }), // use 1-28 to be safe across all months
        fc.integer({ min: 0, max: 11 }),
        fc.integer({ min: 2024, max: 2026 }),
        (day, month, year) => {
          const task = makeTask(1, day, month, year);
          const { unmount } = render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);

          // Navigate to the correct month
          const frozenDate = new Date(YEAR, MONTH, 15, 12, 0, 0);
          const currentYear = frozenDate.getFullYear();
          const currentMonth = frozenDate.getMonth();
          const monthDiff = (year - currentYear) * 12 + (month - currentMonth);

          const navBtn = monthDiff >= 0
            ? screen.getByRole('button', { name: /bulan berikutnya/i })
            : screen.getByRole('button', { name: /bulan sebelumnya/i });

          for (let i = 0; i < Math.abs(monthDiff); i++) {
            fireEvent.click(navBtn);
          }

          const taskChip = screen.queryByText('Task 1');
          const cell = document.querySelector(`[data-day="${day}"]`);
          const taskInCorrectCell = cell ? cell.textContent.includes('Task 1') : false;

          unmount();
          return taskChip !== null && taskInCorrectCell;
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Property 23: Navigasi bulan memperbarui grid
   * Validates: Requirements 8.5
   */
  it('[PBT] Property 23: navigasi bulan memperbarui label dan jumlah sel', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 6 }),
        fc.boolean(),
        (steps, forward) => {
          const frozenDate = new Date(YEAR, MONTH, 15, 12, 0, 0);
          const { unmount } = render(<CalendarView tasks={[]} onTaskClick={vi.fn()} />);

          const navBtn = forward
            ? screen.getByRole('button', { name: /bulan berikutnya/i })
            : screen.getByRole('button', { name: /bulan sebelumnya/i });

          for (let i = 0; i < steps; i++) {
            fireEvent.click(navBtn);
          }

          const targetDate = new Date(
            frozenDate.getFullYear(),
            frozenDate.getMonth() + (forward ? steps : -steps),
            1
          );
          const expectedLabel = targetDate.toLocaleString('id-ID', {
            month: 'long',
            year: 'numeric',
          });
          const expectedDays = daysInMonth(targetDate.getFullYear(), targetDate.getMonth());

          const labelPresent = screen.queryByText(expectedLabel) !== null;
          const dayCells = document.querySelectorAll('[data-day]');
          const correctDays = dayCells.length === expectedDays;

          unmount();
          return labelPresent && correctDays;
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Property 24: Klik task di CalendarView memanggil callback dengan task yang benar
   * Validates: Requirements 8.6
   */
  it('[PBT] Property 24: klik task memanggil onTaskClick dengan task yang benar', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 100 }),
        fc.string({ minLength: 1, maxLength: 30 }),
        (taskId, title) => {
          const task = {
            id: taskId,
            title,
            description: '',
            status: 'pending',
            deadline: new Date(YEAR, MONTH, 15, 12).toISOString(),
            is_overdue: false,
            created_at: '',
            updated_at: '',
          };
          const onTaskClick = vi.fn();
          const { unmount } = render(<CalendarView tasks={[task]} onTaskClick={onTaskClick} />);

          const chip = screen.queryByText(title);
          if (!chip) {
            unmount();
            return true; // title might collide with day numbers — skip
          }

          fireEvent.click(chip);
          const calledWithCorrectTask = onTaskClick.mock.calls.length === 1 &&
            onTaskClick.mock.calls[0][0].id === taskId;

          unmount();
          vi.clearAllMocks();
          return calledWithCorrectTask;
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Property 25: Overdue task di CalendarView memiliki indikator visual berbeda
   * Validates: Requirements 8.7
   */
  it('[PBT] Property 25: overdue task memiliki class calendar-task--overdue', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 100 }),
        fc.boolean(),
        (taskId, isOverdue) => {
          const task = makeTask(taskId, 15, MONTH, YEAR, {
            is_overdue: isOverdue,
          });
          const { unmount } = render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);

          const chip = screen.queryByText(`Task ${taskId}`);
          if (!chip) {
            unmount();
            return true;
          }

          const hasOverdueClass = chip.className.includes('calendar-task--overdue');
          unmount();
          return hasOverdueClass === isOverdue;
        }
      ),
      { numRuns: 15 }
    );
  });

  /**
   * Property 26: Filter status di CalendarView hanya menampilkan task yang sesuai
   * Validates: Requirements 9.2
   */
  it('[PBT] Property 26: filter status hanya menampilkan task yang sesuai', () => {
    const statuses = ['pending', 'in_progress', 'done'];
    fc.assert(
      fc.property(
        fc.constantFrom(...statuses),
        fc.array(
          fc.record({
            id: fc.integer({ min: 1, max: 1000 }),
            status: fc.constantFrom(...statuses),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        (filterStatus, taskDefs) => {
          // Deduplicate ids
          const seen = new Set();
          const uniqueDefs = taskDefs.filter((t) => {
            if (seen.has(t.id)) return false;
            seen.add(t.id);
            return true;
          });

          const tasks = uniqueDefs.map(({ id, status }) =>
            makeTask(id, 15, MONTH, YEAR, { status })
          );

          const { unmount } = render(<CalendarView tasks={tasks} onTaskClick={vi.fn()} />);

          fireEvent.change(screen.getByRole('combobox', { name: /filter status/i }), {
            target: { value: filterStatus },
          });

          const expectedVisible = uniqueDefs.filter((t) => t.status === filterStatus);
          const expectedHidden = uniqueDefs.filter((t) => t.status !== filterStatus);

          // CalendarView renders at most 3 tasks per cell — only check the first 3 visible tasks
          const visibleToCheck = expectedVisible.slice(0, 3);
          const allVisiblePresent = visibleToCheck.every(
            (t) => screen.queryByText(`Task ${t.id}`) !== null
          );
          const allHiddenAbsent = expectedHidden.every(
            (t) => screen.queryByText(`Task ${t.id}`) === null
          );

          unmount();
          return allVisiblePresent && allHiddenAbsent;
        }
      ),
      { numRuns: 10 }
    );
  });
});
