/**
 * Global auth guard.
 *
 * Public routes (/login, /register) are always accessible.
 * All other routes require authentication. When no in-memory
 * token exists the plugin (auth.client.ts) will already have
 * attempted a silent refresh; if that failed the user is simply
 * not authenticated and gets redirected to /login.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  // SSR: skip — token lives in client memory only
  if (import.meta.server) return

  const { isAuthenticated, authReady } = useAuth()

  // Wait for the client-side auth initialisation (silent refresh) to finish
  // before deciding whether the user is authenticated. Without this, the
  // middleware can run while the auth.client plugin is still in-flight and
  // incorrectly redirect the user to /login.
  if (!authReady.value) {
    await new Promise<void>((resolve) => {
      const stop = watch(authReady, (ready) => {
        if (ready) {
          stop()
          resolve()
        }
      }, { immediate: false })
    })
  }

  const publicPages = ['/login', '/register', '/', '/download', '/about', '/privacy', '/terms', '/license', '/landing']
  const isPublic = publicPages.includes(to.path)

  // Protected route without auth → redirect
  if (!isPublic && !isAuthenticated.value) {
    return navigateTo('/login')
  }
})
