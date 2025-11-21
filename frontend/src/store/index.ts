import { create } from 'zustand'

interface User {
  id: number
  name: string
  email: string
  role: string
}

interface AuthStore {
  user: User | null
  token: string | null
  refreshToken: string | null
  login: (user: User, token: string, refreshToken: string) => void
  logout: () => void
  setUser: (user: User) => void
  restore: () => void
}

// Helper to safely parse user from localStorage
const getStoredUser = (): User | null => {
  try {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: getStoredUser(),
  token: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
  login: (user, token, refreshToken) => {
    localStorage.setItem('accessToken', token)
    localStorage.setItem('refreshToken', refreshToken)
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, token, refreshToken })
  },
  logout: () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
    set({ user: null, token: null, refreshToken: null })
  },
  setUser: (user) => set({ user }),
  restore: () => {
    set({
      user: getStoredUser(),
      token: localStorage.getItem('accessToken'),
      refreshToken: localStorage.getItem('refreshToken')
    })
  }
}))

interface Movie {
  id: number
  title: string
  description: string
  duration_minutes: number
  poster_url: string
  genre: string
}

interface MoviesStore {
  movies: Movie[]
  loading: boolean
  setMovies: (movies: Movie[]) => void
  addMovie: (movie: Movie) => void
  updateMovie: (movie: Movie) => void
  deleteMovie: (id: number) => void
  setLoading: (loading: boolean) => void
}

export const useMoviesStore = create<MoviesStore>((set) => ({
  movies: [],
  loading: false,
  setMovies: (movies) => set({ movies }),
  addMovie: (movie) => set((state) => ({ movies: [...state.movies, movie] })),
  updateMovie: (movie) =>
    set((state) => ({
      movies: state.movies.map((m) => (m.id === movie.id ? movie : m))
    })),
  deleteMovie: (id) =>
    set((state) => ({
      movies: state.movies.filter((m) => m.id !== id)
    })),
  setLoading: (loading) => set({ loading })
}))
