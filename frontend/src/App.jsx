import { Routes, Route, Navigate } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/sonner'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Home from './pages/Home'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import IssueDetailPage from './pages/IssueDetailPage'
import Settings from './pages/Settings'
import McpSettingsPage from './pages/McpSettingsPage'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function App() {
  return (
    <AuthProvider>
      <TooltipProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/projects" element={<PrivateRoute><ProjectList /></PrivateRoute>} />
          <Route path="/projects/:slug" element={<PrivateRoute><ProjectDetail /></PrivateRoute>} />
          <Route path="/projects/:slug/issues/:identifier" element={<PrivateRoute><IssueDetailPage /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
          <Route path="/mcp-settings" element={<PrivateRoute><McpSettingsPage /></PrivateRoute>} />
        </Routes>
        <Toaster position="bottom-right" />
      </TooltipProvider>
    </AuthProvider>
  )
}

export default App
