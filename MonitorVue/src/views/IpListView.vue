<template>
  <div class="container">
    <div class="calendar-container">
      <Card class="centered-title">
        <template #title>IP统计</template>
        <template #content>
          日期:
          <Calendar id="calendar-24h" v-model="date" showTime hourFormat="24" />
          <Button type="button" label="查询" icon="pi pi-search" :loading="loading" @click="fetchData" />

        </template>
      </Card>
    </div>

    <div class="card flex">
      <p class="m-0">
        <Card>
          <template #title>历史总IP数前15</template>
          <template #content>
            <p class="m-0">
              <DataTable :value="ips_data.ips_all">
                <Column field="ip" header="IP">
                  <template #body="{ data }">
                    <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                      {{ data.ip }}
                    </router-link>
                  </template>
                </Column>
                <Column field="count" header="数量"></Column>
              </DataTable>

            </p>
          </template>
        </Card>
      </p>


      <Card>
        <template #title>1天内IP数前15</template>
        <template #content>
          <p class="m-0">
            <DataTable :value="ips_data.ips_day">
              <Column field="ip" header="IP">
                <template #body="{ data }">
                  <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                    {{ data.ip }}
                  </router-link>
                </template>
              </Column>
              <Column field="count" header="数量"></Column>
            </DataTable>

          </p>
        </template>
      </Card>

      <Card>
        <template #title>近1小时内IP数量前15</template>
        <template #content>
          <p class="m-0">
            <DataTable :value="ips_data.ips_hour">
              <Column field="ip" header="IP">
                <template #body="{ data }">
                  <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                    {{ data.ip }}
                  </router-link>
                </template>
              </Column>
              <Column field="count" header="数量"></Column>
            </DataTable>
          </p>
        </template>
      </Card>

      <Card>
        <template #title>近5分钟内IP数前15</template>
        <template #content>
          <p class="m-0">
            <DataTable :value="ips_data.ips_min">
              <Column field="ip" header="IP">
                <template #body="{ data }">
                  <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                    {{ data.ip }}
                  </router-link>
                </template>
              </Column>
              <Column field="count" header="数量"></Column>
            </DataTable>

          </p>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import Button from 'primevue/button';
import Calendar from 'primevue/calendar';
import Card from 'primevue/card';
import { computed, onMounted, ref, } from 'vue';


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
const date = ref(new Date());
const loading = ref(false);

const setDefaultWebsiteId = () => {
  selectedWebSite.value = defaultWebsite // 设置默认网站对象，包含 id 和 domain
}


// 计算属性来格式化日期
const formattedDate = computed(() => {
  // 将日期时间都转换为字符串
  return date.value.toISOString().slice(0, 16).replace('T', ' ');
});

const fetchData = async () => {
  if (!selectedWebSite.value) {
    console.error('Please select a website and dates');
    return;
  }
  websiteId.value = selectedWebSite.value.id;

  // 创建日期的UTC格式
  const utcDate = new Date(date.value.getTime() - (date.value.getTimezoneOffset() * 60000)).toISOString();

  // 开始加载
  loading.value = true;
  try {
    const response = await axiosInstance.get(`api/ip_list/`, {
      params: {
        date: utcDate  // 使用UTC格式的日期
      }
    });

    ips_data.value = response.data;

  } catch (error) {
    console.error('Request failed:', error);
  } finally {
    loading.value = false;
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
