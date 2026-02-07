import * as React from "react"
import api from "@/services/api"

const AuthContext = React.createContext(null)

/**
 * AuthProvider with backend integration and demo mode fallback.
 */
export function AuthProvider({ children }) {
    const [user, setUser] = React.useState(null)
    const [loading, setLoading] = React.useState(true)
    const [isOffline, setIsOffline] = React.useState(false)

    React.useEffect(() => {
        if (api.accessToken) {
            fetchUser()
        } else {
            const savedUser = sessionStorage.getItem("demoUser")
            if (savedUser) {
                setUser(JSON.parse(savedUser))
                setIsOffline(true)
            }
            setLoading(false)
        }
    }, [])

    const fetchUser = async () => {
        try {
            const data = await api.getMe()
            setUser(data)
            setIsOffline(false)
        } catch (error) {
            if (error.message === 'Backend unavailable') {
                setIsOffline(true)
                // Use demo user from session
                const saved = sessionStorage.getItem("demoUser")
                if (saved) setUser(JSON.parse(saved))
            } else {
                api.clearTokens()
            }
        } finally {
            setLoading(false)
        }
    }

    const login = async (email, password) => {
        try {
            await api.login(email, password)
            await fetchUser()
            setIsOffline(false)
            return true
        } catch (error) {
            if (error.message === 'Backend unavailable') {
                // Demo mode fallback
                enterDemoMode('patient', email)
                return true
            }
            throw error
        }
    }

    const loginAsDoctor = async (email, password, nmcNumber) => {
        try {
            // First register as doctor, then login
            await api.register(email, password, 'doctor', `Dr. ${email.split('@')[0]}`)
            await fetchUser()
            setIsOffline(false)
            return true
        } catch (error) {
            if (error.message === 'Backend unavailable') {
                enterDemoMode('doctor', email, nmcNumber)
                return true
            }
            // Try login if already registered
            if (error.message.includes('exists') || error.message.includes('duplicate')) {
                return login(email, password)
            }
            throw error
        }
    }

    const register = async (email, password, fullName) => {
        try {
            await api.register(email, password, 'patient', fullName)
            await fetchUser()
            setIsOffline(false)
            return true
        } catch (error) {
            if (error.message === 'Backend unavailable') {
                enterDemoMode('patient', email, null, fullName)
                return true
            }
            throw error
        }
    }

    const logout = () => {
        api.clearTokens()
        sessionStorage.removeItem("demoUser")
        setUser(null)
        setIsOffline(false)
    }

    const enterDemoMode = (role = 'patient', email, nmcNumber, fullName) => {
        setIsOffline(true)
        const demoUser = {
            id: `demo-${role}`,
            email: email || (role === 'doctor' ? "doctor@hospital.com" : "patient@clinic.com"),
            full_name: fullName || (role === 'doctor' ? "Dr. Demo" : "Demo Patient"),
            role,
            nmc_number: nmcNumber,
        }
        setUser(demoUser)
        sessionStorage.setItem("demoUser", JSON.stringify(demoUser))
    }

    const token = api.accessToken

    return (
        <AuthContext.Provider value={{
            user,
            token,
            login,
            loginAsDoctor,
            logout,
            register,
            loading,
            isOffline,
            enterDemoMode
        }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = React.useContext(AuthContext)
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider")
    }
    return context
}
