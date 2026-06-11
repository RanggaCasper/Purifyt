<script setup lang="ts">
// /landing is no longer used � redirect to /
definePageMeta({ layout: false })
await navigateTo('/', { replace: true })
</script>

<template>
  <div />
</template>
