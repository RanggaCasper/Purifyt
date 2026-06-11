<script setup lang="ts">
definePageMeta({
  title: 'Auto Delete'
})

const autoDeleteStore = useAutoDeleteStore()

const activeTab = ref<'scan' | 'login' | 'accounts'>('scan')

onMounted(() => {
  autoDeleteStore.fetchAccounts().catch(() => {})
})
</script>

<template>
  <div>
    <PageHeader
      :title="$t('autoDelete.title')"
      :description="$t('autoDelete.desc')"
    />

    <!-- Tab buttons -->
    <div class="flex gap-2 mb-6">
      <UButton
        :color="activeTab === 'scan' ? 'primary' : 'neutral'"
        :variant="activeTab === 'scan' ? 'solid' : 'outline'"
        :label="$t('autoDelete.scanDelete')"
        icon="i-lucide-scan-search"
        @click="activeTab = 'scan'"
      />
      <UButton
        :color="activeTab === 'login' ? 'primary' : 'neutral'"
        :variant="activeTab === 'login' ? 'solid' : 'outline'"
        :label="$t('autoDelete.googleLogin')"
        icon="i-lucide-log-in"
        @click="activeTab = 'login'"
      />
      <UButton
        :color="activeTab === 'accounts' ? 'primary' : 'neutral'"
        :variant="activeTab === 'accounts' ? 'solid' : 'outline'"
        :label="$t('autoDelete.accounts')"
        icon="i-lucide-users"
        @click="activeTab = 'accounts'"
      />
    </div>

    <!-- TAB: SCAN & HAPUS -->
    <div
      v-if="activeTab === 'scan'"
      class="grid grid-cols-1 lg:grid-cols-2 gap-6"
    >
      <AutoDeleteScanForm />
      <AutoDeleteScanResults />
    </div>

    <!-- TAB: LOGIN GOOGLE -->
    <div
      v-else-if="activeTab === 'login'"
      class="grid grid-cols-1 lg:grid-cols-2 gap-6"
    >
      <AutoDeleteLoginForm />
      <AutoDeleteLoginResults />
    </div>

    <!-- TAB: AKUN -->
    <div v-else-if="activeTab === 'accounts'">
      <AutoDeleteAccountsTable />
    </div>
  </div>
</template>
