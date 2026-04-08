import TaskCard from './TaskCard';

export default function TaskList({ tasks, onStatusUpdated, onTaskDeleted }) {
  if (tasks.length === 0) {
    return (
      <div className="task-list">
        <p className="task-list__empty">
          <span className="task-list__empty-icon">📋</span>
          Belum ada task. Buat task pertama Anda di atas.
        </p>
      </div>
    );
  }

  return (
    <div className="task-list">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onStatusUpdated={onStatusUpdated}
          onTaskDeleted={onTaskDeleted}
        />
      ))}
    </div>
  );
}
