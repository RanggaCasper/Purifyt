const API_BASE_KEY = '__api_base__'

export const useApiBase = () => {
  const config = useRuntimeConfig()
  const fallback = config.public.apiBase as string
  const state = useState<string>(API_BASE_KEY, () => fallback)

  async function resolve(): Promise<string> {
    state.value = fallback
    return state.value
  }

  return { apiBase: readonly(state), resolveApiBase: resolve }
}
