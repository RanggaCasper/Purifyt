<script setup lang="ts">
import type { Comment } from '~/stores/dataset'

const { effectiveLabel, labelSource } = useCommentHelpers()

const _props = defineProps<{
  comments: Comment[]
  selectedIds: Set<number>
  allOnPageSelected: boolean
  selectedCount: number
  inlineLabelLoading: number | null
  commentPage: number
  commentPerPage: number
}>()

const emit = defineEmits<{
  toggleSelectAll: []
  toggleSelect: [id: number]
  inlineLabel: [commentId: number, label: 0 | 1]
}>()
</script>

<template>
  <div>
    <!-- Table: md and above -->
    <div class="hidden md:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-elevated">
            <th class="px-4 py-3 text-left w-10">
              <input
                type="checkbox"
                class="rounded border-default h-4 w-4 cursor-pointer accent-primary-500"
                :checked="allOnPageSelected"
                :indeterminate="selectedCount > 0 && !allOnPageSelected"
                @change="emit('toggleSelectAll')"
              >
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted w-10">
              #
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted">
              {{ $t('datasetDetail.tableAuthor') }}
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted">
              {{ $t('datasetDetail.tableComment') }}
            </th>
            <th class="px-4 py-3 text-center font-medium text-muted whitespace-nowrap">
              {{ $t('datasetDetail.tableLabel') }}
            </th>
            <th class="px-4 py-3 text-center font-medium text-muted">
              {{ $t('common.actions') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-default">
          <tr
            v-for="(comment, idx) in comments"
            :key="comment.id"
            :class="[
              'transition-colors align-top',
              selectedIds.has(comment.id)
                ? 'bg-primary-50/60 dark:bg-primary-950/40'
                : 'hover:bg-elevated/50'
            ]"
          >
            <td class="px-4 py-3">
              <input
                type="checkbox"
                class="rounded border-default h-4 w-4 cursor-pointer accent-primary-500"
                :checked="selectedIds.has(comment.id)"
                @change="emit('toggleSelect', comment.id)"
              >
            </td>
            <td class="px-4 py-3 text-xs text-muted">
              {{ (commentPage - 1) * commentPerPage + idx + 1 }}
            </td>
            <td class="px-4 py-3 max-w-35">
              <div class="flex items-center gap-1.5 min-w-0">
                <UIcon
                  name="i-lucide-user"
                  class="text-xs text-muted shrink-0"
                />
                <span class="text-xs font-medium text-muted truncate">{{ comment.author }}</span>
              </div>
            </td>
            <td class="px-4 py-3">
              <p
                class="text-sm text-highlighted"
                style="overflow-wrap: anywhere; word-break: break-word"
              >
                {{ comment.comment }}
              </p>
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-col items-center gap-1">
                <LabelBadge
                  v-if="effectiveLabel(comment) !== null"
                  :label="effectiveLabel(comment)!"
                />
                <span
                  v-else
                  class="text-xs text-muted"
                >—</span>
                <span
                  v-if="labelSource(comment) === 'manual'"
                  class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
                >
                  <UIcon
                    name="i-lucide-user-check"
                    class="text-[10px]"
                  />{{ $t('common.manual') }}
                </span>
                <span
                  v-else-if="labelSource(comment) === 'predicted'"
                  class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300"
                >
                  <UIcon
                    name="i-lucide-bot"
                    class="text-[10px]"
                  />{{ $t('common.predicted') }}
                </span>
              </div>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center gap-1">
                <template v-if="inlineLabelLoading === comment.id">
                  <UIcon
                    name="i-lucide-loader-circle"
                    class="animate-spin text-xs text-muted"
                  />
                </template>
                <template v-else>
                  <UButton
                    size="xs"
                    color="error"
                    :variant="comment.label === 1 ? 'solid' : 'ghost'"
                    icon="i-lucide-alert-triangle"
                    :title="$t('datasetDetail.labelAsJudi')"
                    @click="emit('inlineLabel', comment.id, 1)"
                  />
                  <UButton
                    size="xs"
                    color="success"
                    :variant="comment.label === 0 ? 'solid' : 'ghost'"
                    icon="i-lucide-check"
                    :title="$t('datasetDetail.labelAsNormal')"
                    @click="emit('inlineLabel', comment.id, 0)"
                  />
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Card list: mobile only -->
    <div class="md:hidden divide-y divide-default">
      <div
        v-for="comment in comments"
        :key="comment.id"
        :class="[
          'px-4 py-3 transition-colors',
          selectedIds.has(comment.id)
            ? 'bg-primary-50/60 dark:bg-primary-950/40'
            : 'hover:bg-elevated/50'
        ]"
      >
        <div class="flex items-start gap-3">
          <input
            type="checkbox"
            class="mt-1 rounded border-default h-4 w-4 cursor-pointer accent-primary-500 shrink-0"
            :checked="selectedIds.has(comment.id)"
            @change="emit('toggleSelect', comment.id)"
          >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5 mb-1">
              <UIcon
                name="i-lucide-user"
                class="text-xs text-muted shrink-0"
              />
              <span class="text-xs font-medium text-muted truncate">{{ comment.author }}</span>
            </div>
            <p
              class="text-sm text-highlighted"
              style="overflow-wrap: anywhere; word-break: break-word"
            >
              {{ comment.comment }}
            </p>
          </div>
          <div class="shrink-0 flex flex-col items-end gap-1.5">
            <LabelBadge
              v-if="effectiveLabel(comment) !== null"
              :label="effectiveLabel(comment)!"
            />
            <span
              v-else
              class="text-xs text-muted"
            >—</span>
            <span
              v-if="labelSource(comment) === 'manual'"
              class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
            >
              <UIcon
                name="i-lucide-user-check"
                class="text-[10px]"
              />{{ $t('common.manual') }}
            </span>
            <span
              v-else-if="labelSource(comment) === 'predicted'"
              class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300"
            >
              <UIcon
                name="i-lucide-bot"
                class="text-[10px]"
              />{{ $t('common.predicted') }}
            </span>
            <div v-if="inlineLabelLoading === comment.id">
              <UIcon
                name="i-lucide-loader-circle"
                class="animate-spin text-xs text-muted"
              />
            </div>
            <div
              v-else
              class="flex gap-1"
            >
              <UButton
                size="xs"
                color="error"
                :variant="comment.label === 1 ? 'solid' : 'ghost'"
                icon="i-lucide-alert-triangle"
                @click="emit('inlineLabel', comment.id, 1)"
              />
              <UButton
                size="xs"
                color="success"
                :variant="comment.label === 0 ? 'solid' : 'ghost'"
                icon="i-lucide-check"
                @click="emit('inlineLabel', comment.id, 0)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
