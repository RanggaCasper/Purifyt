<script setup lang="ts">
defineProps<{
  to: string
  icon: string
  title: string
  description: string
  iconBg: string
  iconColor: string
  hoverBorder: string
  hoverText: string
}>()
</script>

<template>
  <NuxtLink
    :to="to"
    class="bg-default border border-default rounded-xl p-5 hover:shadow-sm transition-all group"
    :class="hoverBorder"
  >
    <div class="flex items-center gap-3 mb-2">
      <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', iconBg]">
        <UIcon
          :name="icon"
          :class="iconColor"
        />
      </div>
      <h3 :class="['font-medium text-highlighted transition-colors', hoverText]">
        {{ title }}
      </h3>
    </div>
    <p class="text-xs text-muted">{{ description }}</p>
  </NuxtLink>
</template>
