<template>
  <div class="container">
    <div class="input-list">
      <label class="label">网站:</label>
      <InputList class="input" v-model="selectedWebSite" />
      <label class="label">时间：</label>
      <div class="calendar-container">
        <Calendar v-model="dates" selectionMode="range" :manualInput="false" />
      </div>
      <Button label="查询" @click="submit" />
    </div>
    <CardData :websiteData="websiteData" />
    <ChartData :websiteId="websiteId" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import InputList from '@/components/InputList.vue'
import ChartData from '@/components/ChartData.vue'
import CardData from '@/components/CardData.vue'
import axios from 'axios'

const dates = ref()
const selectedWebSite = ref(null)
const websiteData = ref([])
const websiteId = ref(null)
const defaultWebsiteId = 1905

const setTodayAsDefaultDate = () => {
  const today = new Date()
  dates.value = [today, today]
}

const defaultWebsite = { id: defaultWebsiteId, domain: 'us.rajabandot.top' }

const setDefaultWebsiteId = () => {
  selectedWebSite.value = defaultWebsite // 设置默认网站对象，包含 id 和 domain
}

const submit = async () => {
  if (!selectedWebSite.value) {
    console.error('Please select a website and dates')
    return
  }
  const data = {
    id: selectedWebSite.value.id,
    dates: dates.value
  }
  websiteId.value = selectedWebSite.value.id
  console.log('Data:', data)
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/website_list/', data)
    console.log('Response:', response.data)
    websiteData.value = response.data[0]
  } catch (error) {
    console.error('Request failed:', error)
  }
}

onMounted(() => {
  setTodayAsDefaultDate() // 设置默认日期
  setDefaultWebsiteId() // 设置默认网站ID
  submit() // 执行查询
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
.child {
  width: 50%;
}
.input-list {
  display: flex;
  align-items: center; /* 垂直居中 */
  gap: 10px; /* 元素之间的间隙 */
  /* padding-bottom: 30px; 底部填充 */
}

.input,
.calendar-container {
  min-width: 200px; /* 日历最小宽度 */
}
</style>
