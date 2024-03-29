<template>
  <div class="container">
    <div class="calendar-container">
      <InputList v-model="dates" />
      <Button label="查询" @click="fetchData" />
    </div>
    <CardData :websiteData="websiteData" />
    <DataTable :customers="customers" />
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
</style>