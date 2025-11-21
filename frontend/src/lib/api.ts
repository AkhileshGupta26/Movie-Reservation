import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken
          })
          localStorage.setItem('accessToken', data.access_token)
          return api(error.config)
        } catch {
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  signup: (name: string, email: string, password: string) =>
    api.post('/auth/signup', { name, email, password }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken })
}

export const moviesAPI = {
  getAll: (skip = 0, limit = 10) =>
    api.get('/admin/movies', { params: { skip, limit } }),
  getById: (id: number) => api.get(`/admin/movies/${id}`),
  create: (data: any) => api.post('/admin/movies', data),
  update: (id: number, data: any) => api.put(`/admin/movies/${id}`, data),
  delete: (id: number) => api.delete(`/admin/movies/${id}`)
}

export const auditoriumsAPI = {
  getAll: (skip = 0, limit = 10) =>
    api.get('/admin/auditoriums', { params: { skip, limit } }),
  getById: (id: number) => api.get(`/admin/auditoriums/${id}`),
  create: (data: any) => api.post('/admin/auditoriums', data),
  update: (id: number, data: any) => api.put(`/admin/auditoriums/${id}`, data),
  delete: (id: number) => api.delete(`/admin/auditoriums/${id}`)
}

export const seatsAPI = {
  getByAuditorium: (auditoriumId: number) =>
    api.get(`/admin/auditoriums/${auditoriumId}/seats`),
  createBatch: (auditoriumId: number, data: any) =>
    api.post(`/admin/auditoriums/${auditoriumId}/seats/batch`, data),
  delete: (seatId: number) => api.delete(`/admin/seats/${seatId}`)
}

export const showtimesAPI = {
  getAll: (skip = 0, limit = 10) =>
    api.get('/admin/showtimes', { params: { skip, limit } }),
  getById: (id: number) => api.get(`/admin/showtimes/${id}`),
  getSeats: (showtimeId: number) =>
    api.get(`/showtimes/${showtimeId}/seats`),
  create: (data: any) => api.post('/admin/showtimes', data),
  update: (id: number, data: any) => api.put(`/admin/showtimes/${id}`, data),
  delete: (id: number) => api.delete(`/admin/showtimes/${id}`)
}

export const bookingAPI = {
  holdSeats: (showtimeId: number, seatIds: number[]) =>
    api.post(`/showtimes/${showtimeId}/holds`, { seat_ids: seatIds }),
  confirmReservation: (reservationId: number) =>
    api.post(`/reservations/${reservationId}/confirm`)
}

export default api
