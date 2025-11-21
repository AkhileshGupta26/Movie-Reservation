import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/store'
import Navbar from '@/components/Navbar'
import LoginPage from '@/pages/LoginPage'
import SignupPage from '@/pages/SignupPage'
import MoviesPage from '@/pages/MoviesPage'
import AdminPage from '@/pages/AdminPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((state) => state.token)
  return token ? <>{children}</> : <Navigate to="/login" />
}

export default function App() {
  const restore = useAuthStore((state) => state.restore)

  useEffect(() => {
    restore()
  }, [restore])

  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/movies"
          element={
            <ProtectedRoute>
              <MoviesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/movies" />} />
      </Routes>
    </BrowserRouter>
  )
}
