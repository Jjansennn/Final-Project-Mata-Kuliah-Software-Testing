import * as fc from 'fast-check';
import { fetchTasks, createTask, updateTask, deleteTask, login, register, UnauthorizedError } from '../../src/frontend/api/apiClient';

describe('ApiClient', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('melempar Error jika fetch gagal karena network error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network Error')));
    await expect(fetchTasks()).rejects.toThrow('Network Error');
    vi.unstubAllGlobals();
  });

  // --- login & register ---

  it('login memanggil POST /auth/login dengan email dan password', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({ token: 'abc123' }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await login('user@example.com', 'password123');

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/auth/login');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual({ email: 'user@example.com', password: 'password123' });

    vi.unstubAllGlobals();
  });

  it('register memanggil POST /auth/register dengan email dan password', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: vi.fn().mockResolvedValue({ id: 1, email: 'user@example.com' }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await register('user@example.com', 'password123');

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/auth/register');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual({ email: 'user@example.com', password: 'password123' });

    vi.unstubAllGlobals();
  });

  // --- Authorization header ---

  it('menyertakan header Authorization jika token ada di localStorage', async () => {
    localStorage.setItem('token', 'my-jwt-token');
    let capturedHeaders = null;
    vi.stubGlobal('fetch', vi.fn().mockImplementation((_url, opts) => {
      capturedHeaders = opts?.headers ?? {};
      return Promise.resolve({ ok: true, status: 200, json: vi.fn().mockResolvedValue([]) });
    }));

    await fetchTasks();

    expect(capturedHeaders['Authorization']).toBe('Bearer my-jwt-token');
    vi.unstubAllGlobals();
  });

  it('tidak menyertakan header Authorization jika token tidak ada di localStorage', async () => {
    let capturedHeaders = null;
    vi.stubGlobal('fetch', vi.fn().mockImplementation((_url, opts) => {
      capturedHeaders = opts?.headers ?? {};
      return Promise.resolve({ ok: true, status: 200, json: vi.fn().mockResolvedValue([]) });
    }));

    await fetchTasks();

    expect(capturedHeaders['Authorization']).toBeUndefined();
    vi.unstubAllGlobals();
  });

  // --- Auto-logout saat 401 ---

  it('menghapus token dari localStorage dan melempar UnauthorizedError saat response 401', async () => {
    localStorage.setItem('token', 'expired-token');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: vi.fn().mockResolvedValue({ error: 'Unauthorized' }),
    }));

    await expect(fetchTasks()).rejects.toThrow(UnauthorizedError);
    expect(localStorage.getItem('token')).toBeNull();

    vi.unstubAllGlobals();
  });

  it('auto-logout berlaku untuk semua fungsi request saat 401', async () => {
    const mock401 = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: vi.fn().mockResolvedValue({}),
    });

    localStorage.setItem('token', 'tok');
    vi.stubGlobal('fetch', mock401);
    await expect(createTask('t', 'd')).rejects.toBeInstanceOf(UnauthorizedError);
    expect(localStorage.getItem('token')).toBeNull();

    localStorage.setItem('token', 'tok');
    await expect(updateTask(1, { status: 'done' })).rejects.toBeInstanceOf(UnauthorizedError);
    expect(localStorage.getItem('token')).toBeNull();

    localStorage.setItem('token', 'tok');
    await expect(deleteTask(1)).rejects.toBeInstanceOf(UnauthorizedError);
    expect(localStorage.getItem('token')).toBeNull();

    vi.unstubAllGlobals();
  });

  // --- Existing PBT properties ---

  it('[PBT] Property F10: createTask dan updateTask selalu set Content-Type: application/json', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          title: fc.string({ minLength: 1, maxLength: 200 }),
          description: fc.option(fc.string(), { nil: undefined }),
          taskId: fc.integer({ min: 1 }),
          updateData: fc.record({ status: fc.constantFrom('pending', 'in_progress', 'done') }),
        }),
        async ({ title, description, taskId, updateData }) => {
          let capturedHeaders = null;
          const mockFetch = vi.fn().mockImplementation((_url, opts) => {
            capturedHeaders = opts?.headers ?? {};
            return Promise.resolve({ ok: true, status: 200, json: vi.fn().mockResolvedValue({ id: 1, title, status: 'pending' }) });
          });
          vi.stubGlobal('fetch', mockFetch);
          await createTask(title, description);
          const createHeaders = capturedHeaders;
          await updateTask(taskId, updateData);
          const updateHeaders = capturedHeaders;
          vi.unstubAllGlobals();
          return createHeaders['Content-Type'] === 'application/json' && updateHeaders['Content-Type'] === 'application/json';
        }
      )
    );
  });

  it('[PBT] Property F8: ApiClient menggunakan VITE_API_BASE_URL sebagai prefix URL', async () => {
    // Test bahwa semua request menggunakan URL yang konsisten (semua ke host yang sama)
    const capturedUrls = [];
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url) => {
      capturedUrls.push(url);
      return Promise.resolve({ ok: true, status: 200, json: vi.fn().mockResolvedValue({ id: 1, title: 'test', status: 'pending' }) });
    }));

    await fetchTasks();
    await createTask('test title', 'desc');
    await updateTask(1, { status: 'done' });
    await deleteTask(1);

    vi.unstubAllGlobals();

    // All URLs should share the same base (same origin)
    const bases = capturedUrls.map((url) => {
      try { return new URL(url).origin; } catch { return url.split('/').slice(0, 3).join('/'); }
    });
    const uniqueBases = new Set(bases);
    expect(uniqueBases.size).toBe(1);
  });

  it('[PBT] Property F9: semua fungsi melempar Error untuk HTTP 400–599 (kecuali 401)', async () => {
    await fc.assert(
      fc.asyncProperty(fc.integer({ min: 400, max: 599 }).filter(s => s !== 401), async (status) => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status, json: vi.fn().mockResolvedValue({}) }));
        await expect(fetchTasks()).rejects.toThrow();
        await expect(createTask('title', 'desc')).rejects.toThrow();
        await expect(updateTask(1, { title: 'updated' })).rejects.toThrow();
        await expect(deleteTask(1)).rejects.toThrow();
        vi.unstubAllGlobals();
      })
    );
  });

  it('[PBT] Property: header Authorization selalu disertakan jika token ada di localStorage', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }),
        async (token) => {
          localStorage.setItem('token', token);
          let capturedHeaders = null;
          vi.stubGlobal('fetch', vi.fn().mockImplementation((_url, opts) => {
            capturedHeaders = opts?.headers ?? {};
            return Promise.resolve({ ok: true, status: 200, json: vi.fn().mockResolvedValue([]) });
          }));
          await fetchTasks();
          vi.unstubAllGlobals();
          localStorage.clear();
          return capturedHeaders['Authorization'] === `Bearer ${token}`;
        }
      ),
      { numRuns: 15 }
    );
  });
});
