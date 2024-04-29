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
        域名(选填)：
        <InputText type="text" v-model="domain" />
        <Toast />
        <FileUpload ref="fileUpload" name="upload_file" url="/api/upload" accept=".log,application/gzip,.gz"
          :maxFileSize="1000000000" customUpload :auto="false" :multiple="true" />
        <Button label="上传" @click="submit_up" />
      </div>

    </div>

    <CardData :websiteData="websiteData" />
    <p>7天内统计</p>
    <ChartData :websiteId="websiteId" />
  </div>
</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig'
import CardData from '@/components/CardData.vue'
import ChartData from '@/components/ChartData.vue'
import InputList from '@/components/InputList.vue'
import moment from 'moment'
import { useToast } from 'primevue/usetoast'
import { onMounted, ref } from 'vue'


const toast = useToast();
const dates = ref()
const selectedWebSite = ref(null)
const websiteData = ref({
  visitor_totals: 0,
  ip_totals: 0,
  visit_totals: 0,
  data_transfer_totals: 0
});
const websiteId = ref(null)
const defaultWebsiteId = 1905
const domain = ref('')
const logFormat = ref('')
const fileUpload = ref(null)
const csrfToken = ref('')
const history = ref([])  // 历史记录
let pollingInterval = null; // 轮询间隔


const checkTaskStatus = async (taskId) => {
  try {
    const response = await axiosInstance.get(`/api/task-status/${taskId}/`);
    if (response.data.status === 'SUCCESS' || response.data.status === 'FAILURE') {
      toast.add({
        severity: response.data.status === 'SUCCESS' ? 'success' : 'error',
        summary: response.data.status === 'SUCCESS' ? '处理完成' : '处理失败',
        detail: response.data.status === 'SUCCESS' ? '文件已成功处理' : '文件处理失败，请重试',
        life: 3000
      });
      clearInterval(pollingInterval); // 停止轮询
    }
  } catch (error) {
    console.error('状态检查失败:', error);
    // 可以在这里实现重试逻辑或停止轮询
    clearInterval(pollingInterval); // 停止轮询
  }
};


const submit_up = async () => {
  if (fileUpload.value?.files?.length > 0) {
    const file = fileUpload.value.files[0];
    let formData = new FormData();
    formData.append('upload_file', file, file.name);
    formData.append('website', domain.value);
    formData.append('nginx_log_format', logFormat.value);


    try {
      const response = await axiosInstance.post('api/upload/', formData);

      // 保存任务ID
      const taskId = response.data.task_id;

      // 使用taskId进行轮询
      pollingInterval = setInterval(() => checkTaskStatus(taskId), 5000);

      // 保存域名到历史记录
      if (logFormat.value) {
        let logFormatHistory = JSON.parse(localStorage.getItem('logFormatHistory') || '[]');
        if (!logFormatHistory.includes(logFormat.value)) {
          logFormatHistory.push(logFormat.value);
          localStorage.setItem('logFormatHistory', JSON.stringify(logFormatHistory));
        }
      }
      console.log(response)
      // 200为成功400为缺少nginx日志配置
      if (response.status === 202) {
        toast.add({ severity: 'success', summary: '上传成功', detail: response.data.message, life: 3000 });
      }
    } catch (error) {

      if (error.response.status === 401) {
        toast.add({ severity: 'error', summary: '上传失败', detail: '缺少nginx日志配置', life: 3000 });
      } else {
        toast.add({ severity: 'error', summary: '上传失败', detail: '文件上传失败，请重试', life: 3000 });
      }
      // 失败的Toast通知
    }
  } else {
    console.log('没有文件被选中！');
    toast.add({ severity: 'warn', summary: '无文件', detail: '请先选择一个文件', life: 3000 });
  }
};


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
    dates: dates.value.map((date) => moment(date).format('YYYY-MM-DD'))
  }
  websiteId.value = selectedWebSite.value.id
  console.log('Data:', data)
  try {
    const response = await axiosInstance.post('api/website_list/', data)
    console.log('Response:', response.data)
    websiteData.value = response.data
  } catch (error) {
    console.error('Request failed:', error)
  }
}

function clearHistory() {
  // 清空localStorage中的历史记录
  localStorage.removeItem('logFormatHistory');
  // 更新绑定到datalist的数据
  history.value = [];
}

onMounted(async () => {
  try {
    const response = await axiosInstance.get('api/csrf_token/',);
    console.log('CSRF 令牌:', response);
    csrfToken.value = response.data.csrfToken;
  } catch (error) {
    console.error('获取 CSRF 令牌失败:', error);
  }
  setTodayAsDefaultDate() // 设置默认日期
  setDefaultWebsiteId() // 设置默认网站ID
  submit() // 执行查询
  // 加载域名历史记录
  let logFormatHistory = JSON.parse(localStorage.getItem('logFormatHistory') || '[]');
  history.value = logFormatHistory;
})
</script>




<style scoped>
.upload-container {
  display: flex;
  align-items: center;
  /* 垂直居中 */
  padding: 20px;
  gap: 20px;
  /* 组件之间的间隙 */
  background-color: #f8fafc;
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
