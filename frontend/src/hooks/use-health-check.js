import * as React from 'react'
import api from '@/services/api'

/**
 * Hook to check backend health status on mount.
 * Returns { isOnline, isChecking, error, recheck }
 */
export function useHealthCheck() {
    const [isOnline, setIsOnline] = React.useState(null)
    const [isChecking, setIsChecking] = React.useState(true)
    const [error, setError] = React.useState(null)

    const checkHealth = React.useCallback(async () => {
        setIsChecking(true)
        setError(null)

        try {
            const response = await fetch(
                `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/health`,
                { method: 'GET', timeout: 5000 }
            )

            if (response.ok) {
                setIsOnline(true)
            } else {
                setIsOnline(false)
                setError(`HTTP ${response.status}`)
            }
        } catch (err) {
            setIsOnline(false)
            setError(err.message || 'Backend unavailable')
        } finally {
            setIsChecking(false)
        }
    }, [])

    React.useEffect(() => {
        checkHealth()
    }, [checkHealth])

    return { isOnline, isChecking, error, recheck: checkHealth }
}
