import { useEffect, useState } from 'react'
import { showtimesAPI, seatsAPI, bookingAPI } from '@/lib/api'
import { useAuthStore } from '@/store'
import { Calendar, MapPin, Clock, DollarSign } from 'lucide-react'

export default function MoviesPage() {
  const [showtimes, setShowtimes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedShowtime, setSelectedShowtime] = useState<number | null>(null)
  const [seats, setSeats] = useState<any[]>([])
  const [selectedSeats, setSelectedSeats] = useState<number[]>([])
  const [booking, setBooking] = useState(false)
  const user = useAuthStore((state) => state.user)

  useEffect(() => {
    loadShowtimes()
  }, [])

  const loadShowtimes = async () => {
    try {
      setLoading(true)
      const { data } = await showtimesAPI.getAll(0, 20)
      setShowtimes(data.items || data)
    } catch (err) {
      console.error('Failed to load showtimes', err)
    } finally {
      setLoading(false)
    }
  }

  const loadSeats = async (showtimeId: number) => {
    try {
      const { data } = await seatsAPI.getByAuditorium(showtimeId)
      setSeats(data)
      setSelectedSeats([])
    } catch (err) {
      console.error('Failed to load seats', err)
    }
  }

  const handleShowtimeSelect = async (showtimeId: number) => {
    setSelectedShowtime(showtimeId)
    await loadSeats(showtimeId)
  }

  const handleSeatClick = (seatId: number) => {
    setSelectedSeats((prev) =>
      prev.includes(seatId) ? prev.filter((id) => id !== seatId) : [...prev, seatId]
    )
  }

  const handleBooking = async () => {
    if (!selectedShowtime || selectedSeats.length === 0) return

    setBooking(true)
    try {
      const { data } = await bookingAPI.holdSeats(selectedShowtime, selectedSeats)
      alert('Seats booked! Reservation expires in 10 minutes.')
      setSelectedSeats([])
      setSelectedShowtime(null)
    } catch (err) {
      alert('Booking failed. Please try again.')
    } finally {
      setBooking(false)
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400 mb-4">Please login to book movies</p>
          <a href="/login" className="btn-primary">
            Login
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="gradient-text text-4xl font-bold mb-8">Available Showtimes</h1>

        {loading ? (
          <div className="text-center text-slate-400">Loading showtimes...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {showtimes.map((showtime) => (
              <div
                key={showtime.id}
                className="card cursor-pointer hover:border-purple-500/50 transition"
                onClick={() => handleShowtimeSelect(showtime.id)}
              >
                <h3 className="text-xl font-bold mb-4">{showtime.movie?.title}</h3>
                <div className="space-y-2 text-slate-300 mb-4">
                  <div className="flex items-center gap-2">
                    <Calendar size={16} />
                    <span>{new Date(showtime.starts_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock size={16} />
                    <span>{new Date(showtime.starts_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin size={16} />
                    <span>{showtime.auditorium?.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign size={16} />
                    <span>${showtime.base_price}</span>
                  </div>
                </div>
                <button
                  className={`w-full py-2 rounded-lg transition ${
                    selectedShowtime === showtime.id
                      ? 'btn-primary'
                      : 'btn-secondary'
                  }`}
                >
                  {selectedShowtime === showtime.id ? 'Selected' : 'Select'}
                </button>
              </div>
            ))}
          </div>
        )}

        {selectedShowtime && seats.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold mb-6">Select Your Seats</h2>
            <div className="glass p-8 mb-6">
              <div className="grid grid-cols-10 gap-2 mb-6">
                {seats.map((seat) => (
                  <button
                    key={seat.id}
                    onClick={() => handleSeatClick(seat.id)}
                    className={`p-2 rounded text-sm font-semibold transition ${
                      selectedSeats.includes(seat.id)
                        ? 'gradient-primary text-white'
                        : seat.is_booked
                        ? 'bg-red-900 text-slate-400 cursor-not-allowed'
                        : 'bg-slate-700 text-slate-300 hover:bg-purple-600'
                    }`}
                    disabled={seat.is_booked}
                  >
                    {seat.seat_number}
                  </button>
                ))}
              </div>

              <div className="flex justify-between items-center">
                <div className="space-y-2 text-slate-300">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-purple-600 rounded"></div>
                    <span>Selected ({selectedSeats.length})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-slate-700 rounded"></div>
                    <span>Available</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-red-900 rounded"></div>
                    <span>Booked</span>
                  </div>
                </div>

                <button
                  onClick={handleBooking}
                  disabled={booking || selectedSeats.length === 0}
                  className="btn-primary px-8"
                >
                  {booking ? 'Booking...' : `Book ${selectedSeats.length} Seat(s)`}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
