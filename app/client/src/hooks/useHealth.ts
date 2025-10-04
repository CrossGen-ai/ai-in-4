import { useState, useEffect } from 'react'
import { api } from '@/lib/api/client'

/**
 * Hook to check backend health status
 *
 * This hook serves as a working example of the custom hook pattern.
 * See app_docs/patterns/frontend-hooks.md for the full pattern documentation.
 *
 * @example
 * ```tsx
 * function App() {
 *   const { isHealthy, loading } = useHealth()
 *
 *   if (loading) return <div>Checking backend...</div>
 *   if (!isHealthy) return <div>Backend is down!</div>
 *
 *   return <div>Backend is healthy</div>
 * }
 * ```
 *
 * @returns Object containing health status and loading state
 */
export function useHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const result = await api.healthCheck()
        setIsHealthy(result.status === 'healthy')
      } catch {
        setIsHealthy(false)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  return { isHealthy, loading }
}
