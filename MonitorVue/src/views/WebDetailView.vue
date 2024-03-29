<template>
  <div>
    <span>WebDetailView</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'

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

<style scoped>
</style>