<template>
  <Card>
    <template #title>{{ WebsiteDetail.domain }} 网站日志的详细信息</template>
    <template #content>
      <p class="m-0">

      </p>
    </template>
  </Card>
  <FilterDisplay :WebsiteDetail="WebsiteDetail" />

</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import Card from 'primevue/card';          // optional
import FilterDisplay from '@/components/FilterDisplay.vue'; // optional

const route = useRoute()
const WebsiteDetail = ref([])

const fetchData = async () => {
  const websiteId = route.params.id
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/website_detail/' + websiteId + '/')
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