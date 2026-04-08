const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

export class UnauthorizedError extends Error {
  constructor() {
    super('Sesi berakhir. Silakan login kembali.');
    this.name = 'UnauthorizedError';
  }
}

function getBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || BASE_URL;
}

async function request(path, options = {}) {
  const url = `${getBaseUrl()}${path}`;
  const token = localStorage.getItem('token');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    localStorage.removeItem('token');
    throw new UnauthorizedError();
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `HTTP error ${response.status}`);
  }

  return response.json();
}

// Auth
export async function login(email, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email, password) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

// Tasks
export async function fetchTasks() {
  return request('/tasks');
}

export async function createTask(title, description, deadline) {
  return request('/tasks', {
    method: 'POST',
    body: JSON.stringify({ title, description, deadline: deadline || null }),
  });
}

export async function updateTask(id, data) {
  return request(`/tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteTask(id) {
  return request(`/tasks/${id}`, {
    method: 'DELETE',
  });
}
