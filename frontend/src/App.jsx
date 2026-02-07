import { AuthProvider, useAuth } from "@/auth/AuthProvider"
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom"
import { LoginPage } from "@/pages/auth/LoginPage"
import { RegisterPage } from "@/pages/auth/RegisterPage"
import { DoctorLoginPage } from "@/pages/auth/DoctorLoginPage"
import { ClinicalWorkspace } from "@/components/ClinicalWorkspace"

// Protected Route
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background mesh-gradient">
        <div className="glass-panel rounded-xl p-6 flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
          <span className="text-sm text-muted-foreground">Loading...</span>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}

// Auth Router
function AuthRoutes() {
  const navigate = useNavigate()

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <LoginPage
            onNavigate={(path) => navigate(`/${path}`)}
            onLoginSuccess={() => navigate("/")}
          />
        }
      />
      <Route
        path="/register"
        element={
          <RegisterPage
            onNavigate={(path) => navigate(`/${path}`)}
            onLoginSuccess={() => navigate("/")}
          />
        }
      />
      <Route
        path="/doctor-login"
        element={
          <DoctorLoginPage
            onNavigate={(path) => navigate(`/${path}`)}
            onLoginSuccess={() => navigate("/")}
          />
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <ClinicalWorkspace />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AuthRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
