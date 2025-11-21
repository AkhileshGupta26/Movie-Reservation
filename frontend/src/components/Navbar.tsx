import { useAuthStore } from '@/store'
import { LogOut, User } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Navbar() {
  const { user, logout } = useAuthStore()

  return (
    <nav className="bg-slate-900 border-b border-slate-700/50">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2">
          <div className="gradient-text text-2xl font-bold">🎬 CineBook</div>
        </Link>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <Link
                to="/movies"
                className="text-slate-300 hover:text-white transition"
              >
                Movies
              </Link>
              <Link
                to="/bookings"
                className="text-slate-300 hover:text-white transition"
              >
                My Bookings
              </Link>
              {user.role === 'admin' && (
                <Link
                  to="/admin"
                  className="text-slate-300 hover:text-white transition"
                >
                  Admin
                </Link>
              )}
              <div className="flex items-center gap-2 text-slate-300">
                <User size={18} />
                <span>{user.name}</span>
              </div>
              <button
                onClick={() => {
                  logout()
                  window.location.href = '/login'
                }}
                className="btn-secondary flex items-center gap-2"
              >
                <LogOut size={18} />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-secondary">
                Login
              </Link>
              <Link to="/signup" className="btn-primary">
                Sign Up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
