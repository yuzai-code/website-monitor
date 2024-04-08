<template>
  <div class="container">
    <div class="calendar-container">
      网站:
      <InputList class="input" v-model="selectedWebSite" />
      <Button label="查询" @click="fetchData" />
    </div>
    <Card class="centered-title">
      <template #title>IP统计</template>
      <template #content>
        ip统计根据http_x_forwarded_for进行统计
      </template>
    </Card>
    <div class="card flex">
      <p class="m-0">
        <Card>
          <template #title>历史总IP数前10</template>
          <template #content>
            <p class="m-0">
              <DataTable :value="ips_data.ips_all">
                <Column field="key" header="IP">
                  <template #body="slotProps">
                    <!-- 使用 websiteId 作为参数 -->
                    <router-link :to="{ name: 'WebsiteDetail', params: { id: websiteId, ip: slotProps.data.key } }">
                      {{ slotProps.data.key }}
                    </router-link>
                  </template>
                </Column>
                <Column field="doc_count" header="数量"></Column>
              </DataTable>

            </p>
          </template>
        </Card>
      </p>


      <Card>
        <template #title>1天内IP数前10</template>
        <template #content>
          <p class="m-0">
            <DataTable :value="ips_data.ips_day">
              <Column field="key" header="IP">
                <template #body="slotProps">
                  <!-- 使用 websiteId 作为参数 -->
                  <router-link :to="{ name: 'WebsiteDetail', params: { id: websiteId, ip: slotProps.data.key } }">
                    {{ slotProps.data.key }}
                  </router-link>
                </template>
              </Column>
              <Column field="doc_count" header="数量"></Column>
            </DataTable>

          </p>
        </template>
      </Card>

      <Card>
        <template #title>近1小时内IP数量前10</template>
        <template #content>
          <p class="m-0">
            <DataTable :value="ips_data.ips_hour">
              <Column field="key" header="IP">
                <template #body="slotProps">
                  <!-- 使用 websiteId 作为参数 -->
                  <router-link :to="{ name: 'WebsiteDetail', params: { id: websiteId } }">
                    {{ slotProps.data.key }}
                  </router-link>
                </template>
              </Column>
              <Column field="doc_count" header="数量"></Column>
            </DataTable>
          </p>
        </template>
      </Card>

      <Card>
        <template #title>近5分钟内IP数前10</template>
        <template #content>
          <p class="m-0">
            <DataTable :value="ips_data.ips_min">
              <Column field="key" header="IP">
                <template #body="slotProps">
                  <!-- 使用 websiteId 作为参数 -->
                  <router-link :to="{ name: 'WebsiteDetail', params: { id: websiteId } }">
                    {{ slotProps.data.key }}
                  </router-link>
                </template>
              </Column>
              <Column field="doc_count" header="数量"></Column>
            </DataTable>

          </p>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, defineProps } from 'vue';
import InputList from '@/components/InputList.vue';  // 确保路径正确
import axiosInstance from '@/axiosConfig.ts'
import Divider from 'primevue/divider';
import Card from 'primevue/card';
import { on } from 'events';

const ips_data = ref({
  ips_all: [],
  ips_min: [],
  ips_hour: [],
  ips_day: [],
});
const selectedWebSite = ref(null);
const websiteId = ref(null);
const defaultWebsiteId = 1905;
const defaultWebsite = { id: defaultWebsiteId, domain: 'us.rajabandot.top' }

const setDefaultWebsiteId = () => {
  selectedWebSite.value = defaultWebsite // 设置默认网站对象，包含 id 和 domain
}

// const getWebsiteId = (id) => {
//   console.log('Received ID:', id);
//   selectedWebSite.value = id;
// };


const fetchData = async () => {
  if (!selectedWebSite.value) {
    console.error('Please select a website and dates')
    return
  }
  websiteId.value = selectedWebSite.value.id;
  try {
    const response = await axiosInstance.get(`api/ip_list/${websiteId.value}/`);
    ips_data.value = response.data;
    console.log('Fetched data:', ips_data.value);
  } catch (error) {
    console.error('Request failed:', error);
  }
};
onMounted(() => {
  setDefaultWebsiteId();
  fetchData();
});
</script>

<style scoped>
.card {
  display: flex;
  gap: 1rem;
  top: 1rem;
  margin-top: 1rem;
  padding: 1rem;
}

.card>>>.p-card-title {
  text-align: center;
}
</style>
