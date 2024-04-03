<template>
  <AutoComplete v-model="selectedItem" optionLabel="domain" :suggestions="filteredWebsites" @complete="search">
  </AutoComplete>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'

const website = ref([])
const selectedItem = ref(null)
const filteredWebsites = ref([])

onMounted(async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/website_list')
    website.value = response.data
    console.log('Website list:', website.value)
  } catch (error) {
    console.error('Request failed:', error)
  }
})

const search = (event) => {
  if (event.query.trim().length === 0) {
    filteredWebsites.value = [...website.value] // 如果没有查询输入，显示所有网站
  } else {
    filteredWebsites.value = website.value.filter((item) => {
      return item.domain.toLowerCase().includes(event.query.toLowerCase())
    })
  }
}
</script>
