import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const queryClient = useQueryClient()

  const { data: user, isLoading: loading } = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      if (!token) return null
      const res = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Unauthorized')
      return res.json()
    },
    enabled: !!token,
    retry: false,
    staleTime: Infinity,
  })

  useEffect(() => {
    if (!token) {
      queryClient.setQueryData(['me'], null)
    }
  }, [token, queryClient])

  const login = useCallback((newToken) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
    queryClient.clear()
  }, [queryClient])

  const authFetch = useCallback(
    (url, options = {}) => {
      const headers = {
        ...options.headers,
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      return fetch(url, { ...options, headers })
    },
    [token]
  )

  return (
    <AuthContext.Provider value={{ user, token, login, logout, authFetch, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
