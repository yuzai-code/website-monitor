<template>
  <AutoComplete v-model="selectedItem" optionLabel="domain" :suggestions="filteredWebsites" @complete="search"
    @update:modelValue="handleSelectionChange"></AutoComplete>
</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import { onMounted, ref } from 'vue';

const website = ref([])
const selectedItem = ref(null)
const filteredWebsites = ref([])
// const emit = defineEmits(['getWebsiteId'])
const autoCompleteInput = ref('');

const handleSelectionChange = (newValue) => {
  selectedItem.value = newValue;
  autoCompleteInput.value = newValue ? newValue.domain : ''; // 假设newValue包含domain属性
  sessionStorage.setItem('selectedItem', JSON.stringify(newValue));
  // emit('getWebsiteId', newValue ? newValue.id : null);
};


onMounted(async () => {
  // 尝试从 sessionStorage 获取保存的选中项
  const savedItem = sessionStorage.getItem('selectedItem');
  if (savedItem) {
    selectedItem.value = JSON.parse(savedItem);
  }

  try {
    const response = await axiosInstance.get('api/website_list');
    website.value = response.data;
    // 更新 filteredWebsites 以反映可能从 sessionStorage 恢复的选中项
    filteredWebsites.value = [...website.value];
    // console.log('Website list:', website.value);
  } catch (error) {
    console.error('Request failed:', error);
  }
});


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
