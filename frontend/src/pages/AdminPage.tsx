import { useEffect, useState } from 'react'
import { moviesAPI, auditoriumsAPI, showtimesAPI } from '@/lib/api'
import { useAuthStore } from '@/store'
import { Plus, Edit2, Trash2, X } from 'lucide-react'

export default function AdminPage() {
  const [tab, setTab] = useState<'movies' | 'auditoriums' | 'showtimes'>('movies')
  const [movies, setMovies] = useState<any[]>([])
  const [auditoriums, setAuditoriums] = useState<any[]>([])
  const [showtimes, setShowtimes] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<any>({})
  const user = useAuthStore((state) => state.user)

  useEffect(() => {
    if (tab === 'movies') loadMovies()
    else if (tab === 'auditoriums') loadAuditoriums()
    else loadShowtimes()
  }, [tab])

  const loadMovies = async () => {
    try {
      const { data } = await moviesAPI.getAll()
      setMovies(data.items || data)
    } catch (err) {
      console.error('Failed to load movies', err)
    }
  }

  const loadAuditoriums = async () => {
    try {
      const { data } = await auditoriumsAPI.getAll()
      setAuditoriums(data.items || data)
    } catch (err) {
      console.error('Failed to load auditoriums', err)
    }
  }

  const loadShowtimes = async () => {
    try {
      const { data } = await showtimesAPI.getAll()
      setShowtimes(data.items || data)
    } catch (err) {
      console.error('Failed to load showtimes', err)
    }
  }

  const handleAddMovie = async () => {
    if (!formData.title || !formData.duration_minutes || !formData.base_price) {
      alert('Please fill all required fields')
      return
    }

    setLoading(true)
    try {
      await moviesAPI.create(formData)
      setFormData({})
      setShowForm(false)
      loadMovies()
      alert('Movie added successfully!')
    } catch (err) {
      alert('Failed to add movie')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteMovie = async (id: number) => {
    if (!confirm('Are you sure?')) return
    try {
      await moviesAPI.delete(id)
      loadMovies()
    } catch (err) {
      alert('Failed to delete movie')
    }
  }

  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400">Admin access required</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="gradient-text text-4xl font-bold mb-8">Admin Dashboard</h1>

        <div className="flex gap-4 mb-8">
          {(['movies', 'auditoriums', 'showtimes'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg transition capitalize ${
                tab === t ? 'btn-primary' : 'btn-secondary'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <button
          onClick={() => setShowForm(!showForm)}
          className="btn-primary flex items-center gap-2 mb-6"
        >
          <Plus size={18} />
          Add {tab.slice(0, -1)}
        </button>

        {showForm && tab === 'movies' && (
          <div className="card mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Add New Movie</h3>
              <button onClick={() => setShowForm(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Movie Title"
                value={formData.title || ''}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="input-field"
              />
              <input
                type="text"
                placeholder="Genre"
                value={formData.genre || ''}
                onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
                className="input-field"
              />
              <input
                type="number"
                placeholder="Duration (minutes)"
                value={formData.duration_minutes || ''}
                onChange={(e) =>
                  setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })
                }
                className="input-field"
              />
              <textarea
                placeholder="Description"
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="input-field"
              />
              <button
                onClick={handleAddMovie}
                disabled={loading}
                className="btn-primary w-full"
              >
                {loading ? 'Creating...' : 'Create Movie'}
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4">
          {tab === 'movies' &&
            movies.map((movie) => (
              <div key={movie.id} className="card flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-bold">{movie.title}</h3>
                  <p className="text-slate-400">{movie.genre} • {movie.duration_minutes} min</p>
                </div>
                <div className="flex gap-2">
                  <button className="btn-secondary p-2">
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => handleDeleteMovie(movie.id)}
                    className="btn-secondary p-2 hover:bg-red-900"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}

          {tab === 'auditoriums' &&
            auditoriums.map((aud) => (
              <div key={aud.id} className="card">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold">{aud.name}</h3>
                    <p className="text-slate-400">Capacity: {aud.capacity}</p>
                  </div>
                  <div className="flex gap-2">
                    <button className="btn-secondary p-2">
                      <Edit2 size={18} />
                    </button>
                    <button className="btn-secondary p-2 hover:bg-red-900">
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}

          {tab === 'showtimes' &&
            showtimes.map((showtime) => (
              <div key={showtime.id} className="card">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold">{showtime.movie?.title}</h3>
                    <p className="text-slate-400">
                      {new Date(showtime.starts_at).toLocaleString()} @ {showtime.auditorium?.name}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button className="btn-secondary p-2">
                      <Edit2 size={18} />
                    </button>
                    <button className="btn-secondary p-2 hover:bg-red-900">
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}
