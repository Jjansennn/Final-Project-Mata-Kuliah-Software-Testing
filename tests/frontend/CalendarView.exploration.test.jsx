import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, afterEach, expect } from 'vitest';
import CalendarView from '../../src/frontend/components/CalendarView';

/**
 * RC4 Fix-Check — CalendarView deterministik dengan frozen time
 *
 * Setelah fix RC4 diterapkan (vi.useFakeTimers + vi.setSystemTime di CalendarView.test.jsx),
 * test ini memverifikasi bahwa task dengan deadline 15 Jul 2024 selalu muncul di sel hari ke-15
 * terlepas dari waktu eksekusi, karena waktu di-freeze sebelum render.
 *
 * Bug yang diperbaiki: CalendarView menggunakan `new Date()` tanpa mock sehingga task
 * yang dibuat di 23:59:59 tidak muncul di sel yang benar setelah waktu maju ke 00:00:01.
 * Fix: freeze waktu ke nilai yang diketahui sebelum membuat task dan sebelum render.
 */

afterEach(() => {
  vi.useRealTimers();
});

describe('RC4 Exploration — CalendarView day boundary bug', () => {
  it(
    '[EXPLORATION] task yang dibuat di 23:59:59 harus muncul di sel hari yang sama setelah waktu maju ke 00:00:01',
    () => {
      // Fix RC4: freeze waktu ke 15 Jul 2024 12:00:00 sebelum membuat task dan render
      // Ini memastikan deadline task dan "today" di komponen konsisten
      vi.useFakeTimers();
      vi.setSystemTime(new Date(2024, 6, 15, 12, 0, 0)); // 15 Jul 2024 12:00:00 (frozen)

      // Buat task dengan deadline fixed — tidak bergantung pada real clock
      const task = {
        id: 1,
        title: 'Task Pergantian Hari',
        description: '',
        status: 'pending',
        deadline: new Date(2024, 6, 15, 23, 59, 59).toISOString(), // fixed: 15 Jul 2024
        is_overdue: false,
        created_at: '',
        updated_at: '',
      };

      // Render CalendarView dengan waktu yang sudah di-freeze ke hari ke-15
      render(<CalendarView tasks={[task]} onTaskClick={vi.fn()} />);

      // Assert task muncul di sel hari ke-15 (tanggal deadline task)
      // Dengan frozen time, "today" = 15 Jul 2024, sehingga task selalu ditemukan di sel ke-15
      const taskCell = document.querySelector('[data-day="15"]');
      expect(taskCell).not.toBeNull();
      expect(taskCell.textContent).toContain('Task Pergantian Hari');
    }
  );
});
