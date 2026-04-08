import './StatusBadge.css';

const STATUS_MAP = {
  pending: { className: 'badge--pending', label: 'Pending' },
  in_progress: { className: 'badge--in-progress', label: 'In Progress' },
  done: { className: 'badge--done', label: 'Done' },
};

export default function StatusBadge({ status }) {
  const { className, label } = STATUS_MAP[status] ?? { className: '', label: status };
  return <span className={`badge ${className}`}>{label}</span>;
}
