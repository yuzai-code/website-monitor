<template>
    <div class="md:container md:mx-auto">
        <div class="box-content">
            <label class="label ">域名：</label>
            <AutoComplete class="mx-2" v-model="value" dropdown :suggestions="items" @complete="fetchDomains" />
            <Button label="查询" @click="search" icon="pi pi-search" :loading="loading" />
        </div>
        <div class="flex">
            <p class="text-blue-600">{{ domain }} 最近一个月相关数据的汇总</p>
        </div>
        <div class="card">
            <Chart type="line" :data="chartData" :options="chartOptions" class="h-30rem" />
        </div>
    </div>
</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import { bytesToGB } from '@/utils/bytesToGB';
import Chart from 'primevue/chart';
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

onMounted(() => {
    fetchData();
    fetchDomains();
    chartOptions.value = setChartOptions();
})

const route = useRoute();
const chartData = ref();
const chartOptions = ref();
const value = ref("");  // 搜索框的值
const items = ref([]);  // 搜索框的建议
const loading = ref(false);  // 是否正在加载
const domain = ref();


// 设置图表选项
const setChartOptions = () => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--text-color-secondary');
    const surfaceBorder = documentStyle.getPropertyValue('--surface-border');

    return {
        maintainAspectRatio: false,
        aspectRatio: 0.6,
        plugins: {
            legend: {
                labels: {
                    color: textColor
                }
            }
        },
        scales: {
            x: {
                ticks: {
                    color: textColorSecondary
                },
                grid: {
                    color: surfaceBorder
                }
            },
            y: {
                ticks: {
                    color: textColorSecondary
                },
                grid: {
                    color: surfaceBorder
                }
            }
        }
    };
}


// 设置图表数据
const setChartData = (data) => {
    const labels = data.map((item) => item.visit_date); // 时间作为x轴
    const google_bot = data.map((item) => item.google_bot);
    const google_referer = data.map((item) => item.google_referer);
    const ips = data.map((item) => item.ips);
    const visits = data.map((item) => item.visits);
    const data_transfers = data.map((item) => bytesToGB(item.data_transfers));
    console.log('data_transfers:', data[0]['domain'])
    return {
        labels: labels,
        datasets: [
            {
                label: 'Google Bot',
                data: google_bot,
                fill: false,
                borderColor: '#42A5F5'
            },
            {
                label: 'Google 来源',
                data: google_referer,
                fill: false,
                borderColor: '#66BB6A'
            },
            {
                label: 'IP数',
                data: ips,
                fill: false,
                borderColor: '#FFA726'
            },
            {
                label: '访问量',
                data: visits,
                fill: false,
                borderColor: '#EF5350'
            },
            {
                label: '流量GB',
                data: data_transfers,
                fill: false,
                borderColor: '#AB47BC'
            }
        ],
    }
}
// 从后端api获取所有的domain
const fetchDomains = async () => {
    try {
        const response = await axiosInstance.get('api/website_list/', {
            params: {
                domain_list: true
            }
        });
        items.value = response.data.map((item) => item.domain);
    } catch (error) {
        console.error('Request failed:', error);
    }
}

// 从后端api获取数据
const fetchData = async () => {
    // 从路由参数中获取网站名称
    const domain_params = route.params.domain;
    try {
        const response = await axiosInstance.get('api/website_detail/', {
            params: {
                domain: domain_params,
                search_text: value.value,
            }
        })
        console.log('Response:', response.data);
        // 设置图表数据
        chartData.value = setChartData(response.data);
        domain.value = response.data[0]['domain']
        // loading.value = true;
    } catch (error) {
        console.error(error);
    }
}

// // 搜索框的搜索事件
const search = async () => {
    console.log('Search:', value.value);
    try {
        const response = await axiosInstance.get('api/website_detail/', {
            params: {
                domain: value.value,
            }
        })
        // items.value = response.data.map((item) => item.domain);
        // 等待加载
        loading.value = true;
        setTimeout(() => {
            loading.value = false;
        }, 2000);
        // 设置图表数据
        chartData.value = setChartData(response.data);
        domain.value = response.data[0]['domain'];
    } catch (error) {
        console.error('Request failed:', error);
    }
}


</script>
<style scoped>
.card {
    background-color: var(--surface-color);
    border-radius: 0.5rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
</style>