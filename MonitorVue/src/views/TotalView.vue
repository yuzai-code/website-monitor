<template>
    <Card>
        <template #title>汇总</template>
        <template #content>
            <p class="m-0">
                汇总
            </p>
        </template>
    </Card>
    <div class="card">
        <Chart type="line" :data="chartData" :options="chartOptions" class="h-30rem" />
    </div>
</template>
<script setup>
import { ref, onMounted,  } from 'vue'
import Chart from 'primevue/chart'
import axiosInstance from '@/axiosConfig.ts'



const chartData = ref(null)
const chartOptions = ref(null)

const transformDataToChartData = (apiData) => {
    const labels = apiData.map(entry => entry.visit_date);
    const totalVisitData = apiData.map(entry => entry.google_visit);
    const totalIPData = apiData.map(entry => entry.total_ip);
    const googleBotData = apiData.map(entry => entry.google_bot);

    return {
        labels,
        datasets: [
            {
                label: '来自 Google 的访问量',
                data: totalVisitData,
                fill: false,
                borderColor: '#42A5F5',
                tension: 0.1
            },
            {
                label: '所有 IP',
                data: totalIPData,
                fill: false,
                borderColor: '#FFA726',
                tension: 0.1
            },
            {
                label: 'Googlebot 数',
                data: googleBotData,
                fill: false,
                borderColor: '#66BB6A',
                tension: 0.1
            }
        ]
    };
}


const setChartData = async () => {
    // 获取存储的Token
    const token = localStorage.getItem('authToken');
    try {
        const response = await axiosInstance.get(`api/total/`, {
            headers: {
                // 添加Token到请求头
                'Authorization': `Token ${token}`
            }
        })
        console.log('Chart data:', response.data)
        chartData.value = transformDataToChartData(response.data)
    } catch (error) {
        console.error('Failed to fetch chart data:', error)
        // 可能还需要设置 chartData.value 为一些默认值以防错误
    }
}

const setChartOptions = () => {
    const documentStyle = getComputedStyle(document.documentElement)
    const textColor = documentStyle.getPropertyValue('--text-color')
    const textColorSecondary = documentStyle.getPropertyValue('--text-color-secondary')
    const surfaceBorder = documentStyle.getPropertyValue('--surface-border')

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
    }
}




onMounted(() => {

    setChartData()
    chartOptions.value = setChartOptions()
})
</script>

<style scoped>
.card {
    background-color: var(--surface-color);
    border-radius: 0.5rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
</style>