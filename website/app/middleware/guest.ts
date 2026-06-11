/**
 * Guest-only middleware.
 * Redirects authenticated users away from pages like /login and /register.
 *
 * Usage: definePageMeta({ middleware: ['guest'] })
 */
export default defineNuxtRouteMiddleware(() => {
  if (import.meta.server) return

  const { isAuthenticated } = useAuth()

  if (isAuthenticated.value) {
    return navigateTo('/dashboard')
  }
})
