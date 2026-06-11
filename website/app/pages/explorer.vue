<script setup lang="ts">
definePageMeta({
  title: 'Explorer'
})

const mode = ref<'video' | 'channel'>('video')
</script>

<template>
  <div>
    <PageHeader
      :title="$t('explorer.title')"
      :description="$t('explorer.desc')"
    />

    <!-- Mode toggle -->
    <div class="flex gap-2 mb-6">
      <UButton
        :color="mode === 'video' ? 'primary' : 'neutral'"
        :variant="mode === 'video' ? 'solid' : 'outline'"
        :label="$t('explorer.video')"
        icon="i-lucide-play"
        @click="mode = 'video'"
      />
      <UButton
        :color="mode === 'channel' ? 'primary' : 'neutral'"
        :variant="mode === 'channel' ? 'solid' : 'outline'"
        :label="$t('explorer.channel')"
        icon="i-lucide-tv"
        @click="mode = 'channel'"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Form -->
      <ExplorerVideoForm v-if="mode === 'video'" />
      <ExplorerChannelForm v-else />

      <!-- Results -->
      <ExplorerResultPanel />
    </div>
  </div>
</template>
