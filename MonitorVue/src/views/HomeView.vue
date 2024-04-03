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

 
    <div class="upload-container">
      上传nginx日志文件:
      <div class="card-upload">
        域名：
        <InputText type="text" v-model="value" />
      </div>
      <div class="card-upload">
        日志格式：
        <InputText type="text" v-model="value" />
      </div>
      <div class="upload-button-container">
        <Toast />
        <FileUpload mode="basic" name="demo[]" url="/api/upload" accept=".log,.txt,application/zip,application/x-tar"
          :maxFileSize="1000000000" @upload="onUpload" />
      </div>
    </div>

    <CardData :websiteData="websiteData" />
    <p>7天内统计</p>
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
    websiteData.value = response.data
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
.upload-container {
  display: flex;
  align-items: center;
  /* 垂直居中 */
  justify-content: space-around;
  /* 在主轴上平均分布 */
  padding: 20px;
  gap: 20px;
  /* 组件之间的间隙 */
  background-color: #f5f5f5;
  /* 背景色 */
  border-radius: 8px;
  /* 圆角边框 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  /* 盒子阴影 */
}

.card-upload {
  flex: 1;
  /* flex项目的扩展比例 */
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  /* 输入框和标签之间的间隙 */
}

.card-upload>InputText {
  flex-grow: 1;
  /* 输入框占据剩余空间 */
}

.upload-button-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  /* 上传按钮的容器宽度 */
}

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
  align-items: center;
  /* 垂直居中 */
  gap: 10px;
  /* 元素之间的间隙 */
  /* padding-bottom: 30px; 底部填充 */
}

.input,
.calendar-container {
  min-width: 200px;
  /* 日历最小宽度 */
}
</style>
