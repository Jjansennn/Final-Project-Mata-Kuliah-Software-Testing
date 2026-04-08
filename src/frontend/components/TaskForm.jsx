import { useState } from 'react';
import { createTask } from '../api/apiClient';

export default function TaskForm({ onTaskCreated }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [deadline, setDeadline] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();

    if (!title.trim()) {
      setError('Title wajib diisi dan tidak boleh kosong.');
      return;
    }

    setError(null);
    setSubmitting(true);

    // Convert datetime-local value to ISO 8601, or null if empty
    const deadlineISO = deadline ? new Date(deadline).toISOString() : null;

    try {
      const newTask = await createTask(title, description || undefined, deadlineISO);
      onTaskCreated(newTask);
      setTitle('');
      setDescription('');
      setDeadline('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <h2>Tambah Task Baru</h2>

      <div className="task-form__field">
        <label htmlFor="task-title">Title</label>
        <input
          id="task-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Judul task"
        />
      </div>

      <div className="task-form__field">
        <label htmlFor="task-description">Description</label>
        <textarea
          id="task-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Deskripsi (opsional)"
        />
      </div>

      <div className="task-form__field">
        <label htmlFor="task-deadline">Deadline (opsional)</label>
        <input
          id="task-deadline"
          type="datetime-local"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
        />
      </div>

      {error && <p className="task-form__error" role="alert">{error}</p>}

      <button type="submit" className="task-form__submit" disabled={submitting}>
        {submitting ? 'Menyimpan...' : '+ Tambah Task'}
      </button>
    </form>
  );
}
