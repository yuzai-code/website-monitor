<template>
  <div class="container">
    <div class="calendar-container">
      <label class="label">网站：</label>
      <div class="card flex justify-content-center">
        <!-- <InputList class="input" v-model="selectedItem" @update:selectedItem="selectedItem = $event" /> -->
      </div>

      <Button label="查询" @click="submit" />

    </div>

    <DataTable :customers="customers" @reach-last-page="handleLastPageReached" />
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import DataTable from '@/components/DataTable.vue'
import InputList from '@/components/InputList.vue'
import axiosInstance from '@/axiosConfig'


const customers = ref([])
const selectedItem = ref(null);
const afterKey = ref(null);

const handleLastPageReached = () => {
  // 当 DataTable 组件触发 reach-last-page 事件时，调用此函数
  console.log('Last page reached,12312312');
  // 用于加载下一页数据
  submit();
};

const submit = async () => {
  let searchText;
  // 检查selectedItem是对象还是字符串
  if (typeof selectedItem.value === 'object' && selectedItem.value !== null) {
    searchText = selectedItem.value.domain; // 如果是对象，则使用domain属性
  } else {
    searchText = selectedItem.value; // 否则，直接使用selectedItem的值
  }


  try {
    const response = await axiosInstance.get('api/website_list/', {
      params: {
        after_key: afterKey.value
      }
    })
    console.log('Response:', response.data);
    const newData = response.data.website_list;
    // 将新获取的数据与已有的数据拼接起来
    customers.value = customers.value.concat(newData);
    afterKey.value = response.data.after_key;
    console.log(afterKey.value);
  } catch (error) {
    console.error('Request failed:', error);
  }
}

// 页面加载时，不带搜索词调用 submit 获取所有数据
onMounted(() => {
  // 尝试从 sessionStorage 恢复 selectedItem 的值
  const savedItem = sessionStorage.getItem('selectedItem');
  if (savedItem) {
    selectedItem.value = JSON.parse(savedItem);
    // 因为 selectedItem 可能是对象或字符串，根据保存时的格式恢复
  }

  // 页面加载时调用 submit 获取数据，可能使用恢复的 selectedItem 进行搜索
  submit();
});
// 监听 selectedItem 的变化，并根据其值调用 submit 进行搜索
watch(selectedItem, () => {

  submit()
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