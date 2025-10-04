# Frontend Custom Hook Pattern

This document shows the standard pattern for creating custom React hooks.

## Overview

Custom hooks in this application follow React best practices:
- Hooks are stored in `app/client/src/hooks/`
- Names start with `use` prefix (e.g., `useHealth`, `useUsers`)
- Encapsulate stateful logic and side effects
- Return object with named properties for clarity
- Handle loading, error, and data states

## Basic Hook Structure

```typescript
// app/client/src/hooks/useYourFeature.ts
import { useState, useEffect } from 'react'
import { api } from '@/lib/api/client'

interface YourData {
  id: number
  name: string
}

/**
 * Hook to fetch and manage your feature data
 *
 * @example
 * const { data, loading, error } = useYourFeature()
 */
export function useYourFeature() {
  const [data, setData] = useState<YourData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.yourEndpoint()
        setData(result)
      } catch (err) {
        setError(err as Error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, []) // Empty deps array = fetch once on mount

  return { data, loading, error }
}
```

## Usage in Components

```typescript
import { useYourFeature } from '@/hooks/useYourFeature'

function MyComponent() {
  const { data, loading, error } = useYourFeature()

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error: {error.message}</div>
  }

  if (!data) {
    return <div>No data available</div>
  }

  return (
    <div>
      <h1>{data.name}</h1>
      <p>ID: {data.id}</p>
    </div>
  )
}
```

## Hook with Parameters

```typescript
export function useUser(userId: number) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      setLoading(true)
      try {
        const result = await api.getUser(userId)
        setUser(result)
      } catch (err) {
        setError(err as Error)
      } finally {
        setLoading(false)
      }
    }

    fetchUser()
  }, [userId]) // Re-fetch when userId changes
}
```

## Hook with Refetch Function

```typescript
export function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getUsers()
      setUsers(result)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  // Return refetch function for manual refresh
  return { users, loading, error, refetch: fetchUsers }
}

// Usage:
// const { users, loading, refetch } = useUsers()
// <button onClick={refetch}>Refresh</button>
```

## Hook with Mutations (POST/PUT/DELETE)

```typescript
export function useCreateItem() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const createItem = async (data: CreateItemData) => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.createItem(data)
      return result
    } catch (err) {
      setError(err as Error)
      throw err // Re-throw so caller can handle
    } finally {
      setLoading(false)
    }
  }

  return { createItem, loading, error }
}

// Usage:
// const { createItem, loading, error } = useCreateItem()
// await createItem({ name: 'New Item' })
```

## Hook with Polling

```typescript
export function useRealtimeData(intervalMs: number = 5000) {
  const [data, setData] = useState<Data | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getData()
        setData(result)
        setError(null)
      } catch (err) {
        setError(err as Error)
      } finally {
        setLoading(false)
      }
    }

    // Initial fetch
    fetchData()

    // Set up polling
    const interval = setInterval(fetchData, intervalMs)

    // Cleanup on unmount
    return () => clearInterval(interval)
  }, [intervalMs])

  return { data, loading, error }
}
```

## Adding API Methods

Before creating a hook, add the API method to `app/client/src/lib/api/client.ts`:

```typescript
// app/client/src/lib/api/client.ts
export const api = {
  // Existing methods
  async healthCheck() {
    return apiRequest<{ status: string }>('/health')
  },

  // Add your new method
  async getUsers() {
    return apiRequest<User[]>('/users')
  },

  async getUser(id: number) {
    return apiRequest<User>(`/users/${id}`)
  },

  async createUser(data: CreateUserData) {
    return apiRequest<User>('/users', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}
```

## Type Definitions

Define types in `app/client/src/lib/api/types.ts` or component-specific type files:

```typescript
// app/client/src/lib/api/types.ts
export interface User {
  id: number
  name: string
  email: string
}

export interface CreateUserData {
  name: string
  email: string
}
```

## Working Example

See `app/client/src/hooks/useHealth.ts` for a complete working implementation:

```typescript
import { useState, useEffect } from 'react'
import { api } from '@/lib/api/client'

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
```

## Best Practices

1. **Name with 'use' prefix** - Required by React for hooks
2. **Return object, not array** - `{ data, loading }` is clearer than `[data, loading]`
3. **Handle all states** - loading, error, and data/success states
4. **Cleanup effects** - Return cleanup functions in useEffect when needed
5. **Type everything** - Use TypeScript for all state and return values
6. **Keep focused** - One hook should do one thing well
7. **Document with JSDoc** - Add @example and parameter descriptions

## Common Patterns

### Conditional Fetching
```typescript
export function useConditionalData(shouldFetch: boolean) {
  const [data, setData] = useState(null)

  useEffect(() => {
    if (!shouldFetch) return

    fetchData()
  }, [shouldFetch])

  return { data }
}
```

### Debounced Hook
```typescript
export function useSearch(query: string, delay: number = 500) {
  const [results, setResults] = useState([])

  useEffect(() => {
    const timeout = setTimeout(async () => {
      if (query) {
        const data = await api.search(query)
        setResults(data)
      }
    }, delay)

    return () => clearTimeout(timeout)
  }, [query, delay])

  return { results }
}
```

### Local Storage Persistence
```typescript
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    const stored = localStorage.getItem(key)
    return stored ? JSON.parse(stored) : initialValue
  })

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value))
  }, [key, value])

  return [value, setValue] as const
}
```

## Testing Hooks

Test hooks using `@testing-library/react`:

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useYourHook } from './useYourHook'

test('fetches data successfully', async () => {
  const { result } = renderHook(() => useYourHook())

  expect(result.current.loading).toBe(true)

  await waitFor(() => {
    expect(result.current.loading).toBe(false)
  })

  expect(result.current.data).toBeDefined()
})
```

## See Also

- [React Hooks Documentation](https://react.dev/reference/react)
- [API Client](../../app/client/src/lib/api/client.ts)
- Working example: `app/client/src/hooks/useHealth.ts`
- TypeScript types: `app/client/src/lib/api/types.ts`
