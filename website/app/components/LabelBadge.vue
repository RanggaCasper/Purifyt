<script setup lang="ts">
defineProps<{
  label: number
}>()
</script>

<template>
  <span
    :class="[
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      label === 1
        ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400'
        : 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400'
    ]"
  >
    {{ label === 1 ? $t('common.judi') : $t('common.normal') }}
  </span>
</template>
