<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  icon: string
  description?: string
  trend?: number
  color?: 'blue' | 'red' | 'green' | 'yellow' | 'neutral'
}>()
</script>

<template>
  <div class="bg-default border border-default rounded-xl p-5 hover:shadow-sm transition-shadow">
    <div class="flex items-start justify-between">
      <div class="space-y-2">
        <p class="text-sm font-medium text-muted">
          {{ title }}
        </p>
        <p class="text-2xl font-semibold text-highlighted">
          {{ value }}
        </p>
        <p
          v-if="description"
          class="text-xs text-muted"
        >
          {{ description }}
        </p>
      </div>
      <div
        :class="[
          'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
          color === 'red' ? 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400'
          : color === 'green' ? 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400'
            : color === 'yellow' ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-950 dark:text-yellow-400'
              : 'bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400'
        ]"
      >
        <UIcon
          :name="icon"
          class="text-xl"
        />
      </div>
    </div>
    <div
      v-if="trend !== undefined"
      class="mt-3 flex items-center gap-1 text-xs"
    >
      <UIcon
        :name="trend >= 0 ? 'i-lucide-trending-up' : 'i-lucide-trending-down'"
        :class="trend >= 0 ? 'text-green-500' : 'text-red-500'"
      />
      <span :class="trend >= 0 ? 'text-green-600' : 'text-red-600'">
        {{ Math.abs(trend) }}%
      </span>
    </div>
  </div>
</template>
