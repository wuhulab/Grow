import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

const dockerHttp = axios.create({
  baseURL: '/api',
  timeout: 60000
})

export default api

export const systemApi = {
  overview: () => api.get('/system/overview').then(r => r.data),
  network: () => api.get('/system/network').then(r => r.data),
  diskio: () => api.get('/system/diskio').then(r => r.data),
  info: () => api.get('/system/info').then(r => r.data)
}

export const dockerApi = {
  status: () => dockerHttp.get('/docker/status').then(r => r.data),
  containers: () => dockerHttp.get('/docker/containers').then(r => r.data),
  images: () => dockerHttp.get('/docker/images').then(r => r.data),
  action: (id, action) => dockerHttp.post(`/docker/containers/${id}/action`, { action }).then(r => r.data),
  logs: (id, tail = 200) => dockerHttp.get(`/docker/containers/${id}/logs`, { params: { tail } }).then(r => r.data)
}

export const processApi = {
  list: (sort_by = 'cpu', limit = 200) => api.get('/process/list', { params: { sort_by, limit } }).then(r => r.data),
  kill: (pid, force = false) => api.post(`/process/${pid}/kill`, { force }).then(r => r.data)
}

export const filesApi = {
  list: (path) => api.get('/files/list', { params: path ? { path } : {} }).then(r => r.data),
  roots: () => api.get('/files/roots').then(r => r.data),
  read: (path) => api.get('/files/read', { params: { path } }).then(r => r.data),
  write: (path, content) => api.post('/files/write', { path, content }).then(r => r.data),
  remove: (path) => api.post('/files/delete', { path }).then(r => r.data),
  mkdir: (path) => api.post('/files/mkdir', { path }).then(r => r.data),
  rename: (src, dst) => api.post('/files/rename', { src, dst }).then(r => r.data)
}

export const notesApi = {
  get: () => api.get('/notes/').then(r => r.data),
  save: (content) => api.post('/notes/', { content }).then(r => r.data)
}

export function formatBytes(bytes) {
  if (bytes == null) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  let i = 0
  let v = bytes
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(v < 10 && i > 0 ? 2 : v < 100 ? 1 : 0)} ${units[i]}`
}

export function formatSpeed(bytesPerSec) {
  return formatBytes(bytesPerSec) + '/s'
}
