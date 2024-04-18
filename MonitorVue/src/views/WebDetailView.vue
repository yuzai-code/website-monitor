<template>
  <Card>
    <!-- <template #title>{{ WebsiteDetail.domain }} 网站日志的详细信息</template> -->
    <template #content>
      <p class="m-0">

      </p>
    </template>
  </Card>
  <!-- <FilterDisplay  :data="WebsiteDetail" /> -->
  <div class="card p-fluid">
    <DataTable v-model:filters="filters" :value="WebsiteDetail" editMode="cell" filterDisplay="row" paginator :rows="10"
      @page="onPage">
      <Column field="domain" header="Domain" :sortable="true" :filter="true">
        <template #filter="{ filterModel, filterCallback }">
          <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
            placeholder="按 Domain 过滤" />
        </template>
      </Column>

      <Column field="remote_addr" header="Remote Address" :sortable="true" :filter="true">
        <template #filter="{ filterModel, filterCallback }">
          <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
            placeholder="按 Remote Address 过滤" />
        </template>
      </Column>

      <!-- 为 visit_time 使用 Calendar 作为筛选器 -->
      <Column field="visit_time" header="Visit Time" :sortable="true">
                <template v-slot:body="{ data }">
                    {{ formatDateTime(data.visit_time) }}
                </template>
                <template #filter="{ filterModel, filterCallback }">
                    <Calendar v-model="filterModel.value" @input="filterCallback" class="p-column-filter"
                        placeholder="按日期过滤" />
                </template>
            </Column>

      <!-- 为 http_referer 使用 InputText 作为筛选器 -->
      <Column field="http_referer" header="http_referer" :filter="true">
        <template #filter="{ filterModel, filterCallback }">
          <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
            placeholder="" />
        </template>
      </Column>

      <!-- 为 path 使用 InputText 作为筛选器 -->
      <Column field="path" header="路径" :filter="true">
                <template v-slot:body="{ data }">
                    {{ cleanPath(data.path) }}
                </template>
                <template #filter="{ filterModel, filterCallback }">
                    <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
                        placeholder="按路径过滤" />
                </template>
            </Column>

      <!-- 为 user_agent 使用 InputText 作为筛选器 -->
      <Column field="user_agent" header="User Agent" :filter="true">
        <template #filter="{ filterModel, filterCallback }">
          <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
            placeholder="按 user_agent 过滤" />
        </template>
      </Column>

      <!-- 为 data_transfer 使用 InputText 作为筛选器 -->
      <Column field="data_transfer" header="流量" :sortable="true">
        <template #filter="{ filterModel, filterCallback }">
          <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
            placeholder="" />
        </template>
      </Column>

      <!-- 为 status_code 使用 Dropdown 作为筛选器 -->
      <Column field="status_code" header="Status Code" :filter="true">
        <template #filter="{ filterModel, filterCallback }">
          <Dropdown v-model="filterModel.value" @change="filterCallback" :options="statuses" optionLabel="label"
            optionValue="value" 
            :showClear="true" />
        </template>
      </Column>

      <!-- 为 malicious_request 使用 TriStateCheckbox 作为筛选器 -->
      <Column field="malicious_request" header="是否恶意请求" :filter="true">
        <template #filter="{ filterModel, filterCallback }">
          <Dropdown v-model="filterModel.value" @change="filterCallback" :options="malicious_requests" optionLabel="label"
            optionValue="value" 
            :showClear="true" />
        </template>
      </Column>

      <!-- 为 method 使用 Dropdown 作为筛选器 -->
      <Column field="method" header="Method" :filter="true">
        <template v-slot:body="{ data }">
                    {{ cleanmethods(data.method) }}

        </template>
        <template #filter="{ filterModel, filterCallback }">
          <Dropdown v-model="filterModel.value" @change="filterCallback" :options="methods" optionLabel="label"
            optionValue="value" 
            :showClear="true" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axiosInstance from '@/axiosConfig'
import { useRoute } from 'vue-router'
import Card from 'primevue/card';          // optional
import { FilterMatchMode } from 'primevue/api';
import Dropdown from 'primevue/dropdown';      // optional

const route = useRoute()  // 获取路由参数
const WebsiteDetail = ref([])
const new_last_sort_value = ref(null)
const totalRecords = ref(null) // 总页数
const currentPage = ref(null)  // 当前页

const onPage = (event) => {
  const { first, rows } = event;
  currentPage.value = first / rows + 1;
  const totalPages = Math.ceil(totalRecords.value / rows);
  // console.log(`Current page: ${currentPage.value}, Total pages: ${totalPages}`);
  if (currentPage.value === totalPages) {
    fetchData()
  }
}


const statuses = ref([
  { label: '200', value: '200' },
  { label: '404', value: '404' },
  { label: '500', value: '500' },
  { label: '412', value: '412' },
  // Add other statuses as needed
]);

const methods = ref([
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  // { label: 'PUT', value: 'PUT' },
  // { label: 'DELETE', value: 'DELETE' },
  // Add other methods as needed
]);

const malicious_requests = ref([
  {label: 'true', value: true},
  {label: 'false', value: false}
])

// 更新列定义，使其匹配您的数据
const columns = ref([
  { field: 'domain', header: 'domain', sortable: true, filter: true },
  { field: 'remote_addr', header: 'Remote Address', sortable: true, filter: true },
  { field: 'request_time', header: 'Request Time', sortable: true, filter: true },
  { field: 'http_referer', header: 'http_referer', sortable: true, filter: true },
  { field: 'user_agent', header: 'User Agent' },
  { field: 'path', header: 'path' },
  { field: 'data_transfer', header: 'Data Transfer', sortable: true },
  { field: 'visit_time', header: 'Visit Time', sortable: true },
  { field: 'status_code', header: 'status_code', filter: true },
  { field: 'malicious_request', header: '是否恶意请求', filter: true },
  { field: 'method', header: 'method', filter: true }
]);
const filters = ref({
  'domain': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  'remote_addr': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  'request_time': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  'http_referer': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  'user_agent': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  'path': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  'visit_time': { value: null, matchMode: FilterMatchMode.DATE_IS },
  'data_transfer': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  'status_code': { value: null, matchMode: FilterMatchMode.EQUALS },
  'malicious_request': { value: null, matchMode: FilterMatchMode.EQUALS },
  'method': { value: null, matchMode: FilterMatchMode.EQUALS },
});

const formatDateTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString(); // 将返回本地格式的日期和时间
};

const cleanPath = (pathValue) => {
    if (Array.isArray(pathValue) && pathValue.length > 0) {
        return pathValue[0];  // 返回数组中的第一个元素，假设数组里只有一个URL字符串
    }
    return pathValue;  // 如果不是数组，直接返回原值
};

const cleanmethods = (methodValue) => {
    if (Array.isArray(methodValue) && methodValue.length > 0) {
        return methodValue[0];  // 返回数组中的第一个元素，假设数组里只有一个URL字符串
    }
    return methodValue;  // 如果不是数组，直接返回原值

};

const fetchData = async () => {
  const ip = route.params.ip
  // 获取存储的Token
  const token = localStorage.getItem('authToken');
  try {
    const response = await axiosInstance.get('api/website_detail/', {
      headers: {
        // 添加Token到请求头
        'Authorization': `Token ${token}`
      },
      params: {
        ip: ip,
        new_last_sort_value: new_last_sort_value.value
      }

    })
    console.log('Website detail:', response.data)
    WebsiteDetail.value = WebsiteDetail.value.concat(response.data.website_detail)
    totalRecords.value = WebsiteDetail.value.length
    new_last_sort_value.value = response.data.new_last_sort_value
  } catch (error) {
    console.error('Request failed:', error)
  }
}


onMounted(() => {
  fetchData()
})
</script>

<style scoped></style>