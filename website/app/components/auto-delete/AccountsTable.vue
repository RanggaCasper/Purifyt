<script setup lang="ts">
const autoDeleteStore = useAutoDeleteStore()
const toast = useToast()
const { t } = useI18n()

const deleteAccountLoading = ref<string | null>(null)

async function loadAccounts() {
  try {
    await autoDeleteStore.fetchAccounts()
  } catch {
    toast.add({ title: t('autoDelete.loadAccountsFailed'), color: 'error' })
  }
}

async function handleDeleteAccount(email: string) {
  deleteAccountLoading.value = email
  try {
    await autoDeleteStore.deleteAccount(email)
    toast.add({ title: t('autoDelete.cookieDeleted', { email }), color: 'success' })
  } catch {
    toast.add({ title: t('autoDelete.cookieDeleteFailed'), color: 'error' })
  } finally {
    deleteAccountLoading.value = null
  }
}

onMounted(() => loadAccounts())
</script>

<template>
  <DataCard
    :loading="autoDeleteStore.accountsLoading"
    :empty="autoDeleteStore.accounts.length === 0 && !autoDeleteStore.accountsLoading"
    :empty-title="$t('autoDelete.noAccountsYet')"
    :empty-description="$t('autoDelete.loginFirst')"
    empty-icon="i-lucide-users"
  >
    <!-- Desktop table -->
    <div class="hidden md:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default bg-elevated">
            <th class="px-4 py-3 text-left font-medium text-muted w-10">
              #
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted">
              {{ $t('autoDelete.tableEmail') }}
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted">
              {{ $t('autoDelete.tableChannel') }}
            </th>
            <th class="px-4 py-3 text-right font-medium text-muted">
              {{ $t('autoDelete.tableCookies') }}
            </th>
            <th class="px-4 py-3 text-center font-medium text-muted">
              {{ $t('common.status') }}
            </th>
            <th class="px-4 py-3 text-left font-medium text-muted">
              {{ $t('autoDelete.tableUpdated') }}
            </th>
            <th class="px-4 py-3 text-center font-medium text-muted">
              {{ $t('common.actions') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-default">
          <tr
            v-for="(account, idx) in autoDeleteStore.accounts"
            :key="account.id"
            class="hover:bg-elevated/50 transition-colors"
          >
            <td class="px-4 py-3 text-xs text-muted">
              {{ idx + 1 }}
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <UIcon
                  name="i-lucide-mail"
                  class="text-muted shrink-0"
                />
                <span class="font-medium text-highlighted">{{ account.email }}</span>
              </div>
            </td>
            <td class="px-4 py-3 text-muted">
              {{ account.channel_name }}
            </td>
            <td class="px-4 py-3 text-right font-medium text-highlighted tabular-nums">
              {{ account.cookie_count }}
            </td>
            <td class="px-4 py-3 text-center">
              <span
                :class="[
                  'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium',
                  account.is_active && account.file_exists
                    ? 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400'
                    : 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400'
                ]"
              >
                <span
                  :class="[
                    'w-1.5 h-1.5 rounded-full',
                    account.is_active && account.file_exists ? 'bg-green-500' : 'bg-red-500'
                  ]"
                />
                {{
                  account.is_active && account.file_exists
                    ? $t('common.active')
                    : $t('common.inactive')
                }}
              </span>
            </td>
            <td class="px-4 py-3 text-xs text-muted whitespace-nowrap">
              {{
                new Date(account.updated_at).toLocaleDateString('en-GB', {
                  day: '2-digit',
                  month: 'short',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })
              }}
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center">
                <UButton
                  variant="ghost"
                  color="error"
                  icon="i-lucide-trash-2"
                  size="xs"
                  :loading="deleteAccountLoading === account.email"
                  @click="handleDeleteAccount(account.email)"
                />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile card list -->
    <div class="md:hidden divide-y divide-default">
      <div
        v-for="account in autoDeleteStore.accounts"
        :key="account.id"
        class="px-4 py-4 space-y-2"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2 min-w-0">
            <div class="w-9 h-9 bg-blue-100 dark:bg-blue-950 rounded-lg flex items-center justify-center shrink-0">
              <UIcon
                name="i-lucide-user"
                class="text-blue-600 dark:text-blue-400"
              />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-highlighted truncate">
                {{ account.email }}
              </p>
              <p class="text-xs text-muted">
                {{ account.channel_name }}
              </p>
            </div>
          </div>
          <UButton
            variant="ghost"
            color="error"
            icon="i-lucide-trash-2"
            size="xs"
            :loading="deleteAccountLoading === account.email"
            @click="handleDeleteAccount(account.email)"
          />
        </div>
        <div class="flex items-center gap-3 text-xs text-muted">
          <span>{{ account.cookie_count }} {{ $t('autoDelete.cookies') }}</span>
          <span
            :class="[
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
              account.is_active && account.file_exists
                ? 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400'
                : 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400'
            ]"
          >
            {{
              account.is_active && account.file_exists
                ? $t('common.active')
                : $t('common.inactive')
            }}
          </span>
          <span>{{ new Date(account.updated_at).toLocaleDateString('en-GB') }}</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div
      v-if="autoDeleteStore.accounts.length > 0"
      class="px-4 py-3 border-t border-default"
    >
      <span class="text-xs text-muted">
        {{ autoDeleteStore.accounts.length }} {{ $t('autoDelete.accountsRegistered') }}
      </span>
    </div>
  </DataCard>
</template>
