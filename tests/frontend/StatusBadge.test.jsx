import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import StatusBadge from '../../src/frontend/components/StatusBadge';

describe('StatusBadge', () => {
  it('merender span untuk status pending', () => {
    const { container } = render(<StatusBadge status="pending" />);
    expect(container.querySelector('span')).toBeInTheDocument();
  });

  it('menampilkan teks "Pending" untuk status pending', () => {
    render(<StatusBadge status="pending" />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('menampilkan teks "In Progress" untuk status in_progress', () => {
    render(<StatusBadge status="in_progress" />);
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('menampilkan teks "Done" untuk status done', () => {
    render(<StatusBadge status="done" />);
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('[PBT] Property F2: untuk setiap status valid, StatusBadge merender teks label yang sesuai', () => {
    const labelMap = { pending: 'Pending', in_progress: 'In Progress', done: 'Done' };
    fc.assert(
      fc.property(fc.constantFrom('pending', 'in_progress', 'done'), (status) => {
        const { unmount } = render(<StatusBadge status={status} />);
        const result = screen.getByText(labelMap[status]) !== null;
        unmount();
        return result;
      })
    );
  });
});
