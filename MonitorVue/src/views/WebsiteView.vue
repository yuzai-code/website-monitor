<template>
  <div class="container">
    <div class="calendar-container">
      <label class="label">时间：</label>
      <Calendar v-model="dates" selectionMode="range" :manualInput="false" />
      <Button label="查询" @click="fetchData" />
    </div>

    <DataTable :customers="customers" />
    <!-- <DataTable /> -->
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CardData from '@/components/CardData.vue'
import DataTable from '@/components/DataTable.vue'
import axios from 'axios'

const dates = ref([])
const customers = ref([])

// 定义一个函数来设置初始日期为今天
const setTodayAsDefaultDate = () => {
  const today = new Date()
  dates.value = [today, today] // 设置开始和结束日期都为今天
}

// 将提交逻辑移动到一个单独的函数
const fetchData = async () => {
  const data = {
    dates: dates.value
  }
  try {
    // 假设使用 GET 请求获取客户数据
    const responseSite = await axios.get('http://127.0.0.1:8000/api/website_list/', {
      params: { dates: dates.value }
    })
    console.log('Website list:', responseSite.data)
    customers.value = responseSite.data
  } catch (error) {
    console.error('Request failed:', error)
  }
}

onMounted(() => {
  setTodayAsDefaultDate() // 设置默认日期为今天
  fetchData() // 页面加载时自动获取数据
})
</script>


<style scoped>
.container {
  width: 100%;
  display: flex;
  flex-direction: column;
  flex-wrap: wrap;
  padding: 20px;
  gap: 20px;
}
.calendar-container {
  display: flex;
  gap: 10px;
}
.label {
  align-self: center;
}
</style>