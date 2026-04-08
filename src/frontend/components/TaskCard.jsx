import { useState } from 'react';
import StatusBadge from './StatusBadge';
import * as ApiClient from '../api/apiClient';

const STATUS_OPTIONS = ['pending', 'in_progress', 'done'];

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('id-ID', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default function TaskCard({ task, onStatusUpdated, onTaskDeleted }) {
  const [updating, setUpdating] = useState(false);
  const [localError, setLocalError] = useState(null);

  async function handleStatusChange(e) {
    const newStatus = e.target.value;
    const previousStatus = task.status;
    setUpdating(true);
    setLocalError(null);
    try {
      const updatedTask = await ApiClient.updateTask(task.id, { status: newStatus });
      onStatusUpdated(updatedTask);
    } catch (err) {
      setLocalError(err.message || 'Gagal memperbarui status.');
      onStatusUpdated({ ...task, status: previousStatus });
    } finally {
      setUpdating(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm('Hapus task ini?')) return;
    try {
      await ApiClient.deleteTask(task.id);
      onTaskDeleted(task.id);
    } catch (err) {
      setLocalError(err.message || 'Gagal menghapus task.');
    }
  }

  return (
    <article className={`task-card${task.is_overdue ? ' task-card--overdue' : ''}`}>
      <div className="task-card__header">
        <h3 className="task-card__title">{task.title}</h3>
        <StatusBadge status={task.status} />
      </div>

      {task.description && (
        <p className="task-card__description">{task.description}</p>
      )}

      <div className="task-card__meta">
        <span className="task-card__date">Dibuat: {formatDate(task.created_at)}</span>
        {task.deadline && (
          <span className={`task-card__deadline${task.is_overdue ? ' task-card__deadline--overdue' : ''}`}>
            {task.is_overdue ? '⚠️ Overdue: ' : '⏰ Deadline: '}
            {formatDate(task.deadline)}
          </span>
        )}
      </div>

      {localError && (
        <p className="task-card__error" role="alert">{localError}</p>
      )}

      <div className="task-card__actions">
        <select
          value={task.status}
          onChange={handleStatusChange}
          disabled={updating}
          aria-label="Ubah status"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button className="task-card__delete" onClick={handleDelete} aria-label="Hapus task">
          Hapus
        </button>
      </div>
    </article>
  );
}
