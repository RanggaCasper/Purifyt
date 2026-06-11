export function useCommentHelpers() {
  function effectiveLabel(c: {
    label: number | string | null
    predicted_label: string | null
  }): number | null {
    if (c.label !== null && c.label !== undefined && c.label !== '') return Number(c.label)
    if (c.predicted_label !== null && c.predicted_label !== undefined)
      return Number(c.predicted_label)
    return null
  }

  function labelSource(c: {
    label: number | string | null
    predicted_label: string | null
  }): 'manual' | 'predicted' | null {
    if (c.label !== null && c.label !== undefined && c.label !== '') return 'manual'
    if (c.predicted_label !== null && c.predicted_label !== undefined) return 'predicted'
    return null
  }

  return { effectiveLabel, labelSource }
}
