<template>
  <div class="card">
    <DataTable :value="customers" paginator :rows="10" :rowsPerPageOptions="[10, 20, 50]" tableStyle="min-width: 50rem">
      <Column field="domain" header="网站">
        <!-- <template #body="slotProps">
          <router-link :to="{ name: 'WebsiteDetail', params: { id: slotProps.data.id } }">
            {{ slotProps.data.domain }}
          </router-link>
        </template> -->
      </Column>
      <Column field="visits" header="访问量"></Column>
      <!-- <Column field="visitor_total" header="访客量"></Column> -->
      <Column field="ips" header="IP数"></Column>
      <Column field="data_transfers" header="总流量"></Column>
      <!-- <Column field="error_total" header="错误数"></Column> -->
      <!-- <Column field="malicious_request_total" header="恶意请求"></Column> -->
      <!-- <Column field="deploy_status" header="部署"></Column> -->
      <!-- <Column field="request_per_second" header="每秒请求"></Column> -->
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

// 使用 defineProps 定义接收的 prop
defineProps({
  customers: Array
})
</script>

<style scoped>
@media (max-width: 600px) {

  .card .p-datatable .p-datatable-thead>tr>th,
  .card .p-datatable .p-datatable-tbody>tr>td {
    /* 在屏幕宽度较小的情况下调整字体大小、内边距等 */
    padding: 8px;
    font-size: 0.8rem;
  }
}

.card {
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 0 1rem rgba(0, 0, 0, 0.1);
}
</style>