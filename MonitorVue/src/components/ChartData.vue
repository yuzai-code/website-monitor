<template>
  <div class="card">
    <Chart type="line" :data="chartData" :options="chartOptions" class="h-30rem" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Chart from 'primevue/chart'
import { defineProps } from 'vue'
import axios from 'axios'

const props = defineProps({
  websiteId: Number
})

const chartData = ref(null)
const chartOptions = ref(null)

const dataset = chartData.value?.datasets[0]

const transformDataToChartData = (apiData) => {
  // 提取日期作为图表的 X 轴标签
  const labels = apiData[0].visit_count.map((entry) => entry.visit_time)

  // 提取 visit_count 作为第一个数据集
  const visitCountData = apiData[0].visit_count.map((entry) => entry.visit_count)

  // 提取 data_transfer 作为第二个数据集
  const dataTransferData = apiData[0].data_transfer.map((entry) => entry.data_transfer)

  // 返回图表数据
  return {
    labels: labels,
    datasets: [
      {
        label: '访问量',
        data: visitCountData,
        fill: false,
        borderColor: '#42A5F5',
        tension: 0.1
      },
      {
        label: '数据传输量',
        data: dataTransferData,
        fill: false,
        borderColor: '#FFA726',
        tension: 0.1
      }
    ]
  }
}

const setChartData = async (id) => {
  try {
    const response = await axios.get(`http://127.0.0.1:8000/api/chart_data`, {
      params: { id: id }
    })
    chartData.value = transformDataToChartData(response.data)
    console.log('Chart data:', chartData.value)
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

// 观察 websiteId prop 的变化
watch(
  () => props.websiteId,
  (newId) => {
    if (newId) {
      setChartData(newId)
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (props.websiteId) {
    setChartData(props.websiteId)
  }
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