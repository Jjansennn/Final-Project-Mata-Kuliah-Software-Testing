import { useState } from 'react';

const DAY_HEADERS = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'];
const STATUS_OPTIONS = ['semua', 'pending', 'in_progress', 'done'];

function getMonthLabel(date) {
  return date.toLocaleString('id-ID', { month: 'long', year: 'numeric' });
}

function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfWeek(year, month) {
  return new Date(year, month, 1).getDay();
}

function isSameDay(dateA, dateB) {
  return (
    dateA.getFullYear() === dateB.getFullYear() &&
    dateA.getMonth() === dateB.getMonth() &&
    dateA.getDate() === dateB.getDate()
  );
}

export default function CalendarView({ tasks, onTaskClick }) {
  const today = new Date();
  const [currentMonth, setCurrentMonth] = useState(() => {
    return new Date(today.getFullYear(), today.getMonth(), 1);
  });
  const [statusFilter, setStatusFilter] = useState('semua');

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const daysInMonth = getDaysInMonth(year, month);
  const firstDayOfWeek = getFirstDayOfWeek(year, month);

  const filteredTasks = tasks.filter((task) => {
    if (!task.deadline) return false;
    if (statusFilter !== 'semua' && task.status !== statusFilter) return false;
    return true;
  });

  function getTasksForDay(day) {
    const cellDate = new Date(year, month, day);
    return filteredTasks.filter((task) => {
      const deadlineDate = new Date(task.deadline);
      return isSameDay(deadlineDate, cellDate);
    });
  }

  function prevMonth() {
    setCurrentMonth(new Date(year, month - 1, 1));
  }

  function nextMonth() {
    setCurrentMonth(new Date(year, month + 1, 1));
  }

  // Build grid cells: leading empty cells + day cells
  const cells = [];
  for (let i = 0; i < firstDayOfWeek; i++) {
    cells.push({ type: 'empty', key: `empty-${i}` });
  }
  for (let day = 1; day <= daysInMonth; day++) {
    cells.push({ type: 'day', day, key: `day-${day}` });
  }

  return (
    <div className="calendar-view">
      <div className="calendar-view__controls">
        <button
          className="calendar-view__nav"
          onClick={prevMonth}
          aria-label="Bulan sebelumnya"
        >
          ←
        </button>
        <span className="calendar-view__month-label">{getMonthLabel(currentMonth)}</span>
        <button
          className="calendar-view__nav"
          onClick={nextMonth}
          aria-label="Bulan berikutnya"
        >
          →
        </button>
        <select
          className="calendar-view__filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter status"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="calendar-view__grid">
        {DAY_HEADERS.map((h) => (
          <div key={h} className="calendar-view__day-header">{h}</div>
        ))}
        {cells.map((cell) => {
          if (cell.type === 'empty') {
            return <div key={cell.key} className="calendar-view__cell calendar-view__cell--empty" />;
          }
          const dayTasks = getTasksForDay(cell.day);
          const cellDate = new Date(year, month, cell.day);
          const isToday = isSameDay(cellDate, today);
          return (
            <div
              key={cell.key}
              className={`calendar-view__cell${isToday ? ' calendar-view__cell--today' : ''}`}
              data-day={cell.day}
            >
              <span className="calendar-view__date">{cell.day}</span>
              {dayTasks.slice(0, 3).map((task) => {
                const statusClass = task.is_overdue
                  ? 'calendar-task--overdue'
                  : `calendar-task--${task.status}`;
                return (
                  <button
                    key={task.id}
                    className={`calendar-task ${statusClass}`}
                    onClick={() => onTaskClick(task)}
                    title={task.title}
                  >
                    {task.title}
                  </button>
                );
              })}
              {dayTasks.length > 3 && (
                <span className="calendar-overflow">+{dayTasks.length - 3} lainnya</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
