import React from 'react';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { vi } from 'vitest';
import TaskList from '../../src/frontend/components/TaskList';

vi.mock('../../src/frontend/api/apiClient', () => ({
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}));

describe('TaskList', () => {
  it('[PBT] Property F1: untuk array N task (0–20), TaskList merender tepat N TaskCard', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.integer(),
            title: fc.string({ minLength: 1 }),
            status: fc.constantFrom('pending', 'in_progress', 'done'),
            description: fc.option(fc.string()),
            created_at: fc.string(),
            updated_at: fc.string(),
          }),
          { maxLength: 20 }
        ),
        (tasks) => {
          const { unmount } = render(
            <TaskList tasks={tasks} onStatusUpdated={vi.fn()} onTaskDeleted={vi.fn()} />
          );
          if (tasks.length === 0) {
            const result = screen.queryByText('Belum ada task. Buat task pertama Anda di atas.') !== null;
            unmount();
            return result;
          }
          const cards = screen.getAllByRole('heading', { level: 3 });
          const result = cards.length === tasks.length;
          unmount();
          return result;
        }
      ),
      { numRuns: 20 }
    );
  });
});
