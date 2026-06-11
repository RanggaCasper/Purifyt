/**
 * Client-only plugin — runs once when the Nuxt app starts in the browser.
 *
 * On a page reload the in-memory access token is lost, but the HttpOnly
 * refresh_token cookie may still be valid. This plugin calls
 * useAuth().init() which attempts a silent refresh so the user stays
 * logged in without seeing a flash of the login page.
 */
export default defineNuxtPlugin(async () => {
  const { init } = useAuth()
  await init()
})
