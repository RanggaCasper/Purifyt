<script setup lang="ts">
import type { Dataset } from '~/stores/dataset'

defineProps<{
  datasets: Dataset[]
  page: number
  perPage: number
  deleteLoading: number | null
  sourceLabel: (source: string) => string
  sourceColor: (source: string) => string
}>()

const emit = defineEmits<{
  delete: [id: number]
}>()
</script>

<template>
  <div>
    <!-- Table: md and above -->
    <div class="hidden md:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-elevated">
            <th class="px-4 py-3 text-left font-medium text-muted w-10">
              #
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted">
              {{ $t('datasets.tableName') }}
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted">
              {{ $t('datasets.tableSource') }}
            </th>
            <th class="px-4 py-3 text-right font-medium text-muted">
              {{ $t('datasets.tableComments') }}
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted whitespace-nowrap">
              {{ $t('datasets.tableCreated') }}
            </th>
            <th class="px-4 py-3 text-center font-medium text-muted">
              {{ $t('common.actions') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-default">
          <tr
            v-for="(dataset, idx) in datasets"
            :key="dataset.id"
            class="hover:bg-elevated/50 transition-colors"
          >
            <td class="px-4 py-3 text-xs text-muted">
              {{ (page - 1) * perPage + idx + 1 }}
            </td>
            <td class="px-4 py-3 max-w-xs">
              <NuxtLink
                :to="`/datasets/${dataset.id}`"
                class="group block"
              >
                <p class="font-medium text-highlighted group-hover:text-primary-500 transition-colors truncate">
                  {{ dataset.name }}
                </p>
                <p
                  v-if="dataset.description"
                  class="text-xs text-muted truncate mt-0.5"
                >
                  {{ dataset.description }}
                </p>
              </NuxtLink>
            </td>
            <td class="px-4 py-3">
              <span :class="['inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', sourceColor(dataset.source)]">
                {{ sourceLabel(dataset.source) }}
              </span>
            </td>
            <td class="px-4 py-3 text-right font-medium text-highlighted">
              {{ dataset.comment_count.toLocaleString() }}
            </td>
            <td class="px-4 py-3 text-xs text-muted whitespace-nowrap">
              {{
                new Date(dataset.created_at).toLocaleDateString('id-ID', {
                  day: '2-digit',
                  month: 'short',
                  year: 'numeric'
                })
              }}
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center gap-1">
                <UButton
                  :to="`/datasets/${dataset.id}`"
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-eye"
                  size="xs"
                />
                <UButton
                  variant="ghost"
                  color="error"
                  icon="i-lucide-trash-2"
                  size="xs"
                  :loading="deleteLoading === dataset.id"
                  @click.prevent="emit('delete', dataset.id)"
                />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Card list: mobile only -->
    <div class="md:hidden divide-y divide-default">
      <div
        v-for="dataset in datasets"
        :key="dataset.id"
        class="px-4 py-4 flex items-center justify-between hover:bg-elevated/50 transition-colors"
      >
        <NuxtLink
          :to="`/datasets/${dataset.id}`"
          class="flex-1 min-w-0"
        >
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-blue-100 dark:bg-blue-950 rounded-lg flex items-center justify-center shrink-0">
              <UIcon
                name="i-lucide-database"
                class="text-blue-600 dark:text-blue-400"
              />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-highlighted truncate">{{ dataset.name }}</p>
              <div class="flex flex-wrap items-center gap-1.5 text-xs text-muted mt-0.5">
                <span :class="['inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium', sourceColor(dataset.source)]">
                  {{ sourceLabel(dataset.source) }}
                </span>
                <span>{{ dataset.comment_count.toLocaleString() }} {{ $t('common.comments') }}</span>
                <span>{{ new Date(dataset.created_at).toLocaleDateString('id-ID') }}</span>
              </div>
            </div>
          </div>
        </NuxtLink>
        <div class="flex items-center gap-1 ml-3 shrink-0">
          <UButton
            :to="`/datasets/${dataset.id}`"
            variant="ghost"
            color="neutral"
            icon="i-lucide-eye"
            size="xs"
          />
          <UButton
            variant="ghost"
            color="error"
            icon="i-lucide-trash-2"
            size="xs"
            :loading="deleteLoading === dataset.id"
            @click.prevent="emit('delete', dataset.id)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
