<template>
    <div class="card p-fluid">
        <DataTable v-model:filters="filters" :value="WebsiteDetail.visits" editMode="cell"
            @cell-edit-complete="onCellEditComplete" filterDisplay="row" paginator :rows="10">
            <Column field="remote_addr" header="Remote Address" :sortable="true" :filter="true">
                <template #filter="{ filterModel, filterCallback }">
                    <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
                        placeholder="按 Remote Address 过滤" />
                </template>
            </Column>

            <!-- 为 visit_time 使用 Calendar 作为筛选器 -->
            <Column field="visit_time" header="Visit Time" :sortable="true">
                <template #filter="{ filterModel, filterCallback }">
                    <Calendar v-model="filterModel.value" @update:modelValue="filterCallback" dataType="date"
                        :showTime="true" class="p-column-filter" placeholder="按 Visit Time 过滤" />
                </template>
            </Column>

            <!-- 为 http_x_forwarded_for 使用 InputText 作为筛选器 -->
            <Column field="http_x_forwarded_for" header="http_x_forwarded_for Code" :filter="true">
                <template #filter="{ filterModel, filterCallback }">
                    <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
                        placeholder="" />
                </template>
            </Column>

            <!-- 为 http_x_forwarded_for 使用 InputText 作为筛选器 -->
            <Column field="path" header="路径" :filter="true">
                <template #filter="{ filterModel, filterCallback }">
                    <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
                        placeholder="" />
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
            <Column field="data_transfer" header="流量" :filter="true">
                <template #filter="{ filterModel, filterCallback }">
                    <InputText v-model="filterModel.value" @keydown.enter="filterCallback" class="p-column-filter"
                        placeholder="" />
                </template>
            </Column>

            <!-- 为 status_code 使用 Dropdown 作为筛选器 -->
            <Column field="status_code" header="Status Code" :filter="true">
                <template #filter="{ filterModel, filterCallback }">
                    <Dropdown v-model="filterModel.value" @change="filterCallback" :options="statuses"
                        optionLabel="label" optionValue="value" class="p-column-filter" placeholder="Select One"
                        style="min-width: 12rem" :showClear="true" />
                </template>
            </Column>

            <!-- 为 malicious_request 使用 TriStateCheckbox 作为筛选器 -->
            <Column field="malicious_request" header="是否恶意请求" :filter="true">
                <template #filter="{ filterModel, filterCallback }">
                    <TriStateCheckbox v-model="filterModel.value" @change="filterCallback" class="p-column-filter" />
                </template>
            </Column>

            <!-- 为 method 使用 Dropdown 作为筛选器 -->
            <Column field="method" header="Method" :filter="true">
                <template #filter="{ filterModel, filterCallback }">
                    <Dropdown v-model="filterModel.value" @change="filterCallback" :options="methods"
                        optionLabel="label" optionValue="value" class="p-column-filter" placeholder="Select One"
                        style="min-width: 12rem" :showClear="true" />
                </template>
            </Column>
        </DataTable>
    </div>
</template>



<script setup>
import { ref, defineProps } from 'vue';
import { FilterMatchMode } from 'primevue/api';
import Dropdown from 'primevue/dropdown';
import TriStateCheckbox from 'primevue/tristatecheckbox';

defineProps({
    WebsiteDetail: Object
});
const statuses = ref([
    { label: '200 OK', value: '200' },
    { label: '404 Not Found', value: '404' },
    { label: '500 Internal Server Error', value: '500' },
    // Add other statuses as needed
]);

const methods = ref([
    { label: 'GET', value: 'GET' },
    { label: 'POST', value: 'POST' },
    // { label: 'PUT', value: 'PUT' },
    // { label: 'DELETE', value: 'DELETE' },
    // Add other methods as needed
]);

// 更新列定义，使其匹配您的数据
const columns = ref([
    { field: 'remote_addr', header: 'Remote Address', sortable: true, filter: true },
    { field: 'request_time', header: 'Request Time', sortable: true, filter: true },
    { field: 'http_x_forwarded_for', header: 'http_x_forwarded_for', sortable: true, filter: true },
    { field: 'user_agent', header: 'User Agent' },
    { field: 'path', header: 'path' },
    { field: 'data_transfer', header: 'Data Transfer', sortable: true },
    { field: 'visit_time', header: 'Visit Time', sortable: true },
    { field: 'status_code', header: 'status_code', filter: true },
    { field: 'malicious_request', header: '是否恶意请求', filter: true },
    { field: 'method', header: 'method', filter: true }
]);
const filters = ref({
    'remote_addr': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    'request_time': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    'http_x_forwarded_for': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    'user_agent': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    'path': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    'visit_time': { value: null, matchMode: FilterMatchMode.DATE_IS },
    'data_transfer': { value: null, matchMode: FilterMatchMode.EQUALS },
    'status_code': { value: null, matchMode: FilterMatchMode.EQUALS },
    'malicious_request': { value: null, matchMode: FilterMatchMode.CUSTOM },
    'method': { value: null, matchMode: FilterMatchMode.EQUALS },
});


</script>
