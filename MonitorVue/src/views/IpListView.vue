<template>
  <div class="container">
    <div class="calendar-container">
      <Card class="centered-title">
        <template #title>IP统计</template>
        <template #content>
          日期:
          <Calendar id="calendar-24h" v-model="date" @update:modelValue="updateSelectedDate" dateFormat="yy-mm-dd"
            showTime hourFormat="24" />
          <Button type="button" label="查询" icon="pi pi-search" :loading="loading" @click="fetchData" />

        </template>
      </Card>
    </div>

    <div class="leaderboard flex">

      <div>
            <h3 class="m-0">
              GoogleBot的IP 排行
            </h3>
        <div class="card flex">
          <Card>
          <template #title>一周内总IP数前100</template>
          <template #content>
            <p class="m-0">
              <DataTable :value="ips_data.ips_week_googlebot">
                <Column field="ip" header="IP">
                  <template #body="{ data }">
                    <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                      {{ data.ip }}
                    </router-link>
                  </template>
                </Column>
                <Column field="count" header="数量"></Column>
                <Column field="country" header="国家"></Column>
              </DataTable>

            </p>
          </template>
          </Card>
          <Card>
            <template #title>1天内IP数前100</template>
            <template #content>
              <p class="m-0">
                <DataTable :value="ips_data.ips_day_googlebot">
                  <Column field="ip" header="IP">
                    <template #body="{ data }">
                      <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                        {{ data.ip }}
                      </router-link>
                    </template>
                  </Column>
                  <Column field="count" header="数量"></Column>
                  <Column field="country" header="国家"></Column>
                </DataTable>

              </p>
            </template>
          </Card>

          <Card>
            <template #title>近1小时内IP数量前100</template>
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
                  <Column field="country" header="国家"></Column>
                </DataTable>
              </p>
            </template>
          </Card>

          <Card>
            <template #title>近5分钟内IP数前100</template>
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
                  <Column field="country" header="国家"></Column>
                </DataTable>

              </p>
            </template>
          </Card>
        </div>

      </div>

      <div>
            <h3 class="m-0">
              其他IP 排行
            </h3>
        <div class="card flex">

          <Card>
          <template #title>一周内总IP数前100</template>
          <template #content>
            <p class="m-0">
              <DataTable :value="ips_data.ips_week_not_googlebot">
                <Column field="ip" header="IP">
                  <template #body="{ data }">
                    <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                      {{ data.ip }}
                    </router-link>
                  </template>
                </Column>
                <Column field="count" header="数量"></Column>
                <Column field="country" header="国家"></Column>
              </DataTable>

            </p>
          </template>
      </Card>
      <Card>
        <template #title>1天内IP数前100</template>
        <template #content>
          <p class="m-0">
            <DataTable :value="ips_data.ips_day_not_googlebot">
              <Column field="ip" header="IP">
                <template #body="{ data }">
                  <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip } }">
                    {{ data.ip }}
                  </router-link>
                </template>
              </Column>
              <Column field="count" header="数量"></Column>
              <Column field="country" header="国家"></Column>
            </DataTable>

          </p>
        </template>
      </Card>

      <Card>
        <template #title>近1小时内IP数量前100</template>
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
              <Column field="country" header="国家"></Column>
            </DataTable>
          </p>
        </template>
      </Card>

      <Card>
        <template #title>近5分钟内IP数前100</template>
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
              <Column field="country" header="国家"></Column>
            </DataTable>

          </p>
        </template>
      </Card>
        </div>

      </div>
    </div>
    
  </div>
  
</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import { useFilterStore } from '@/store/filterStore';
import Button from 'primevue/button';
import Calendar from 'primevue/calendar';
import Card from 'primevue/card';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';


const ips_data = ref({
  ips_all: [],
  ips_week_googlebot: [],
  ips_week_not_googlebot: [],
  ips_day_googlebot: [],
  ips_day_not_googlebot: [],
  ips_min: [],
  ips_hour: [],
  ips_day: [],
});

const date = ref(new Date());
const loading = ref(false);
const filterStore = useFilterStore(); // 使用筛选条件store
const toast = useToast();

const updateSelectedDate = (newDate) => {
  // console.log('类型1', typeof newDate);
  filterStore.setDate(newDate);
}

const fetchData = async () => {
  // 创建日期的UTC格式
  const utcDate = new Date(filterStore.selectedDate.getTime() - (filterStore.selectedDate.getTimezoneOffset() * 60000)).toISOString();
  // 开始加载
  loading.value = true;
  try {
    const response = await axiosInstance.get(`api/ip_list/`, {
      params: {
        date: utcDate  // 使用UTC格式的日期
      }
    });

    ips_data.value = response.data;
    console.log('Response:', response.data);
    // 将ips_data存储到store中
    filterStore.setIpsData(response.data);
    if (response.status === 202){
      toast.add({
        severity: 'info',
        summary: '数据处理中',
        detail: '数据处理中，请稍后刷新页面',
        life: 10000
      });
    }
    
  } catch (error) {
    console.error('Request failed:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // 从store中获取日期，判断如果类型是string转换为Date类型
  if (typeof filterStore.selectedDate === 'string') {
    filterStore.setDate(new Date(filterStore.selectedDate));
  }
  date.value = filterStore.selectedDate;
  // 从store中获取ips_data，如果存在则直接赋值
  if (filterStore.ipsData) {
    ips_data.value = filterStore.ipsData;
  } else {
    fetchData();
  }
});
</script>

<style scoped>
.m-0 {
  display: flex;          /* 启用 flexbox 布局 */
  justify-content: center; /* 水平居中 */
  padding: 1rem;
}
.card {
  gap: 1rem;
  top: 1rem;
  margin-top: 1rem;
  padding: 1rem;
}

.card>>>.p-card-title {
  text-align: center;
}
</style>
