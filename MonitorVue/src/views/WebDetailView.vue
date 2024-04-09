<template>
  <Card>
    <template #title>{{ WebsiteDetail.domain }} 网站日志的详细信息</template>
    <template #content>
      <p class="m-0">

      </p>
    </template>
  </Card>
  <FilterDisplay :WebsiteDetail="WebsiteDetail" :ip="route.params.ip" />

</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axiosInstance from '@/axiosConfig.ts'
import { useRoute } from 'vue-router'
import Card from 'primevue/card';          // optional
import FilterDisplay from '@/components/FilterDisplay.vue'; // optional

const route = useRoute()
const WebsiteDetail = ref([])



const fetchData = async () => {
  const websiteId = route.params.id
  // 获取存储的Token
  const token = localStorage.getItem('authToken');
  try {
    const response = await axiosInstance.get('api/website_detail/' + websiteId + '/', {
      headers: {
        // 添加Token到请求头
        'Authorization': `Token ${token}`
      }

    })
    console.log('Website detail:', response.data)
    WebsiteDetail.value = response.data
  } catch (error) {
    console.error('Request failed:', error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped></style>