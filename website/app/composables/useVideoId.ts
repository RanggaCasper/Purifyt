export function useVideoId() {
  function extractVideoId(input: string): string {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
      /^[a-zA-Z0-9_-]{11}$/
    ]
    for (const p of patterns) {
      const match = input.match(p)
      if (match) return match[1] || match[0]
    }
    return input
  }

  return { extractVideoId }
}
