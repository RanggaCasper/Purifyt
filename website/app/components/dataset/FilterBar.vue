<script setup lang="ts">
defineProps<{
  sourceFilter: string
  sources: { label: string, value: string }[]
  perPage: number
  perPageOptions: { label: string, value: number }[]
}>()

const emit = defineEmits<{
  'update:sourceFilter': [value: string]
  'update:perPage': [value: number]
}>()
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
    <div class="flex flex-wrap items-center gap-2">
      <UButton
        v-for="source in sources"
        :key="source.value"
        :label="source.label"
        :color="sourceFilter === source.value ? 'primary' : 'neutral'"
        :variant="sourceFilter === source.value ? 'solid' : 'outline'"
        size="sm"
        @click="emit('update:sourceFilter', source.value)"
      />
    </div>
    <USelect
      :model-value="perPage"
      :items="perPageOptions"
      size="sm"
      class="w-32"
      @update:model-value="emit('update:perPage', Number($event))"
    />
  </div>
</template>
