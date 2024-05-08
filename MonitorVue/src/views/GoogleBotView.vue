<template>
    <div class="container">
        <h1>Googlebot</h1>
        <Card class="mb-4">
            <template #title>域名: {{ domain }}</template>
            <template #content>
                <p class="m-0">
                    显示<strong>Googlebot</strong>的详细信息, 每日请求次数. 点击Googlebot数据查看其IP地址和数量.
                </p>
            </template>
        </Card>
        <Card class="mb-4">
            <template #title>Googlebot的详细信息</template>
            <template #content>
                <DataTable v-if="filteredData" :value="filteredData">
                    <Column field="visit_date" header="日期"></Column>
                    <Column field="google_bot" header="Googlebot">
                        <template #body='slotProps'>
                            <span @click="event => googleBotTemplate(event, slotProps)"> <!-- 添加 event 对象 -->
                                {{ slotProps.data.google_bot }}
                            </span>
                        </template>
                    </Column>

                    <OverlayPanel ref="op">
                        <p>GoogleBot的IP地址和数量</p>
                        <DataTable :value="googlebotIP">
                            <Column field="ip" header="IP地址">
                                <template #body={data}>
                                    <router-link :to="{ name: 'WebsiteDetail', params: { ip: data.ip,
                                        date: date,
                                        domain: domain
                                     } }">
                                    {{data.ip}}
                                    </router-link>
                                </template>
                            </Column>
                            <Column field="count" header="数量"></Column>
                        </DataTable>
                    </OverlayPanel>

                </DataTable>
            </template>
        </Card>
    </div>
</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import Card from 'primevue/card';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import OverlayPanel from 'primevue/overlaypanel';
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();  // 路由
const domain = route.params.domain; // 从路由中获取域名
const googlebotDetail = ref([]); // googlebot详情
const op = ref(null); // 弹窗
const googlebotIP = ref([]); // googlebot IP
const date = ref();  // 日期

// 页面加载时请求数据
onMounted(() => {
    fetchData();
});

// 仅映射日期和Googlebot次数
const filteredData = computed(() => {
  return googlebotDetail.value.map(item => ({
    visit_date: item.visit_date,
    google_bot: item.google_bot,
    domain: item.domain,
  }));
});

const googleBotTemplate = (event, slotProps) => {
    const googleBot = slotProps.data.google_bot;
    date.value = slotProps.data.visit_date; 
    // console.log("googleBotTemplate triggered", slotProps.data);  // 检查是否打印此信息
    fetchGoogleBotIP(googleBot, date.value);
    if (op.value) {
      op.value.toggle(event);  // 使用事件对象来定位 OverlayPanel
    }
};

// 向后端查看Googlebot的IP数据
const fetchGoogleBotIP = async (googleBot,visit_date) => {
    try {
        const response = await axiosInstance.get(`/api/website_detail/googlebot/${domain}/`,
            { params: { 
                google_bot: googleBot,
                visit_date: visit_date
             } });
        // console.log(response.data);
        googlebotIP.value = response.data;
    } catch (error) {
        console.error('Request failed:', error);
    }
}

// 向后端请求数据
const fetchData = async () => {
    try {
        const response = await axiosInstance.get(`/api/website_detail/googlebot/${domain}/`);
        googlebotDetail.value = response.data;
    } catch (error) {
        console.error('Request failed:', error);
    }
}
</script>


<style scoped>
.container {
    padding: 10px;
}

.mb-4 {
    margin-bottom: 2rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
</style>