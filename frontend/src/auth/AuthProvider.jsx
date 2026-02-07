import * as React from "react"

const AuthContext = React.createContext(null)

/**
 * AuthProvider with role-based login (doctor/patient).
 * Doctors require NMC verification before login.
 */
export function AuthProvider({ children }) {
    const [user, setUser] = React.useState(null)
    const [token, setToken] = React.useState(() => localStorage.getItem("token"))
    const [loading, setLoading] = React.useState(true)
    const [isOffline, setIsOffline] = React.useState(false)

    React.useEffect(() => {
        if (token) {
            fetchUser(token)
        } else {
            // Check for saved user in sessionStorage (demo mode persistence)
            const savedUser = sessionStorage.getItem("demoUser")
            if (savedUser) {
                setUser(JSON.parse(savedUser))
                setIsOffline(true)
            }
            setLoading(false)
        }
    }, [token])

    const fetchUser = async (authToken) => {
        try {
            const response = await fetch("http://localhost:8000/api/v1/auth/me", {
                headers: { Authorization: `Bearer ${authToken}` }
            })
            if (response.ok) {
                const data = await response.json()
                setUser(data)
                setIsOffline(false)
            } else if (response.status === 401) {
                logout()
            } else {
                throw new Error("API Error")
            }
        } catch (error) {
            console.warn("Backend unavailable. Checking for local token.")
            setIsOffline(true)
            try {
                const payload = JSON.parse(atob(authToken.split('.')[1]))
                setUser({
                    id: "jwt-user",
                    email: payload.sub || "user@clinical.ai",
                    full_name: "User",
                    role: payload.role || "patient"
                })
            } catch {
                logout()
            }
        } finally {
            setLoading(false)
        }
    }

    // Login as Patient (default)
    const login = async (email, password) => {
        try {
            const formData = new URLSearchParams()
            formData.append("username", email)
            formData.append("password", password)

            const response = await fetch("http://localhost:8000/api/v1/auth/token", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData,
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Invalid credentials")
            }

            const data = await response.json()
            localStorage.setItem("token", data.access_token)
            setToken(data.access_token)
            setIsOffline(false)
            return true
        } catch (error) {
            if (error.message.includes("fetch") || error.message.includes("Failed")) {
                console.warn("Backend unavailable. Using demo mode (patient).")
                setIsOffline(true)
                const demoUser = {
                    id: "demo-patient",
                    email: email || "patient@clinical.ai",
                    full_name: email?.split('@')[0] || "Patient",
                    role: "patient"
                }
                setUser(demoUser)
                sessionStorage.setItem("demoUser", JSON.stringify(demoUser))
                return true
            }
            throw error
        }
    }

    // Login as Doctor (with NMC verification)
    const loginAsDoctor = async (email, password, nmcNumber) => {
        try {
            const formData = new URLSearchParams()
            formData.append("username", email)
            formData.append("password", password)
            formData.append("nmc_number", nmcNumber)

            const response = await fetch("http://localhost:8000/api/v1/auth/doctor-token", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData,
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Invalid credentials")
            }

            const data = await response.json()
            localStorage.setItem("token", data.access_token)
            setToken(data.access_token)
            setIsOffline(false)
            return true
        } catch (error) {
            if (error.message.includes("fetch") || error.message.includes("Failed")) {
                console.warn("Backend unavailable. Using demo mode (doctor).")
                setIsOffline(true)
                const demoUser = {
                    id: "demo-doctor",
                    email: email || "doctor@hospital.com",
                    full_name: `Dr. ${email?.split('@')[0] || "Smith"}`,
                    role: "doctor",
                    nmc_number: nmcNumber
                }
                setUser(demoUser)
                sessionStorage.setItem("demoUser", JSON.stringify(demoUser))
                return true
            }
            throw error
        }
    }

    const register = async (email, password, fullName) => {
        try {
            const response = await fetch("http://localhost:8000/api/v1/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, full_name: fullName }),
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Registration failed")
            }

            await login(email, password)
            return true
        } catch (error) {
            if (error.message.includes("fetch") || error.message.includes("Failed")) {
                console.warn("Backend unavailable. Using demo mode.")
                setIsOffline(true)
                const demoUser = {
                    id: "demo-patient",
                    email: email,
                    full_name: fullName,
                    role: "patient"
                }
                setUser(demoUser)
                sessionStorage.setItem("demoUser", JSON.stringify(demoUser))
                return true
            }
            throw error
        }
    }

    const logout = () => {
        localStorage.removeItem("token")
        sessionStorage.removeItem("demoUser")
        setToken(null)
        setUser(null)
        setIsOffline(false)
    }

    const enterDemoMode = (role = 'patient') => {
        setIsOffline(true)
        const demoUser = {
            id: `demo-${role}`,
            email: role === 'doctor' ? "doctor@hospital.com" : "patient@clinic.com",
            full_name: role === 'doctor' ? "Dr. Demo" : "Demo Patient",
            role: role
        }
        setUser(demoUser)
        sessionStorage.setItem("demoUser", JSON.stringify(demoUser))
    }

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
