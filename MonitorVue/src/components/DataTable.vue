<template>
  <div class="card">
    <DataTable :value="customers" paginator :rows="100" :rowsPerPageOptions="[50, 100, 150]"
    :sortField="sortingStore.sortField" :sortOrder="sortingStore.sortOrder"
      tableStyle="min-width: 50rem" @sort="handleSort" @page="onPage">
      <Column field="domain" header="网站">
        <template #body="slotProps">
          <router-link :to="{ name: 'WebsiteData', params: { domain: slotProps.data.domain } }">
            {{ slotProps.data.domain }}
          </router-link>
        </template>
      </Column>
      <Column field="google_bot" header="GoogleBot" sortable>
        <template #body="slotProps">
          <router-link :to="{
            name: 'GoogleBot', params: {
              domain: slotProps.data.domain,
            }
          }">
            {{ slotProps.data.google_bot }}
          </router-link>
        </template>
      </Column>
      <Column field="google_referer" header="Google来源" sortable></Column>
      <Column field="visits" header="访问量" sortable></Column>
      <!-- <Column field="visitor_total" header="访客量"></Column> -->
      <Column field="ips" header="IP数" sortable></Column>
      <Column field="data_transfers" header="总流量" sortable>
        <template #body="slotProps">
          {{ bytesToGB(slotProps.data.data_transfers) }} GB
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { useFilterStore } from '@/store/filterStore';
import { bytesToGB } from '@/utils/bytesToGB';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import { defineEmits, defineProps, ref, watch } from 'vue';

// 使用 defineProps 定义接收的 prop
const props = defineProps({
  customers: Array
})

const sortingStore = useFilterStore(); // 使用筛选器 store

// 使用 defineEmits 定义自定义事件
const emit = defineEmits(['reach-last-page'])

const handleSort = (event) => {
  sortingStore.setSort(event.sortField, event.sortOrder);
};
// 定义计算属性，动态获取 customers 的长度
const totalRecords = ref(props.customers.length);

// 监听 props.customers 的变化，更新 totalRecords 的值
watch(() => props.customers, (newValue) => {
  // totalRecords.value = newValue.length;
});

const onPage = function (event) {
  const { first, rows } = event;
  const currentPage = first / rows + 1;
  const totalPages = Math.ceil(totalRecords.value / rows);
  // console.log(`Current page: ${currentPage}, Total pages: ${totalPages}`);

  if (currentPage === totalPages) {
    // 触发自定义事件 reach-last-page
    emit('reach-last-page');
    // console.log('Reach last page');
  }
};
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