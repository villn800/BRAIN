import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, authLoading, authError, isAuthenticated } = useAuth()
  const [formData, setFormData] = useState({ identifier: '', password: '' })
  const [formError, setFormError] = useState(null)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setFormError(null)
    if (!formData.identifier || !formData.password) {
      setFormError('Please provide both username/email and password.')
      return
    }
    try {
      await login({
        identifier: formData.identifier.trim(),
        password: formData.password,
      })
      navigate('/')
    } catch (error) {
      const detail = error?.data?.detail || error.message || 'Unable to log in'
      setFormError(detail)
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div>
          <div className="brand">
            <span className="brand-dot" />
            <span>BRAIN Inspiration Vault</span>
          </div>
          <p className="muted">Sign in with your bootstrap admin credentials.</p>
        </div>
        <label className="field">
          <span>Username or Email</span>
          <input
            name="identifier"
            type="text"
            value={formData.identifier}
            onChange={handleChange}
            placeholder="moodboard-admin"
            autoComplete="username"
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </label>
        {(formError || authError) && <p className="error-text">{formError || authError?.message}</p>}
        <button type="submit" disabled={authLoading}>
          {authLoading ? 'Signing in…' : 'Log in'}
        </button>
      </form>
    </div>
  )
}
