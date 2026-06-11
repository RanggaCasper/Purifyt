<script setup lang="ts">
defineProps<{
  searchQuery: string
  labelFilter: 'all' | 'judi' | 'normal' | 'unlabeled'
  commentPerPage: number
  commentPerPageOptions: { label: string, value: number }[]
}>()

const emit = defineEmits<{
  'update:searchQuery': [value: string]
  'update:labelFilter': [value: 'all' | 'judi' | 'normal' | 'unlabeled']
  'update:commentPerPage': [value: number]
}>()
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
    <div class="flex flex-1 items-center gap-2">
      <UInput
        :model-value="searchQuery"
        :placeholder="$t('datasetDetail.searchPlaceholder')"
        icon="i-lucide-search"
        class="flex-1 max-w-xs"
        @update:model-value="emit('update:searchQuery', $event as string)"
      />
      <UButton
        v-if="searchQuery"
        icon="i-lucide-x"
        variant="ghost"
        color="neutral"
        @click="emit('update:searchQuery', '')"
      />
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <UButton
        v-for="f in (['all', 'judi', 'normal', 'unlabeled'] as const)"
        :key="f"
        :label="
          f === 'all'
            ? $t('datasetDetail.all')
            : f === 'judi'
              ? $t('common.judi')
              : f === 'normal'
                ? $t('common.normal')
                : $t('common.predict')
        "
        :color="labelFilter === f ? 'primary' : 'neutral'"
        :variant="labelFilter === f ? 'solid' : 'outline'"
        size="sm"
        @click="emit('update:labelFilter', f)"
      />
      <USelect
        :model-value="commentPerPage"
        :items="commentPerPageOptions"
        size="sm"
        class="w-32"
        @update:model-value="emit('update:commentPerPage', Number($event))"
      />
    </div>
  </div>
</template>
