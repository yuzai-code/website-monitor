<template>
  <div class="container">
    <div class="calendar-container">
      <label class="label">网站：</label>
      <div class="card flex justify-content-center">
        <AutoComplete v-model="value" dropdown :suggestions="items" @complete="search" />
      </div>

      <Button label="查询" @click="submit" />

    </div>

    <DataTable :customers="customers" @reach-last-page="handleLastPageReached" />
  </div>
</template>
<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import DataTable from '@/components/DataTable.vue';
import { onMounted, ref } from 'vue';


const customers = ref([])
const afterKey = ref(null);
const value = ref("");
const items = ref([]);

const search = async (event) => {
  console.log('Search:', event.query);
  try {
    const response = await axiosInstance.get('api/website_list/', {
      params: {
        search_text: event.query
      }
    })
    items.value = response.data.website_list.map((item) => item.domain);
    customers.value = response.data.website_list;
  } catch (error) {
    // console.error('Request failed:', error);
  }
}

const handleLastPageReached = () => {
  // 当 DataTable 组件触发 reach-last-page 事件时，调用此函数
  console.log('Last page reached,12312312');
  // 用于加载下一页数据
  submit();
};

const submit = async () => {

  try {
    const response = await axiosInstance.get('api/website_list/', {
      params: {
        after_key: afterKey.value,
        search_text: value.value
      }
    })
    console.log('Response:', response.data);
    const newData = response.data.website_list;
    if (response.data.after_key === null) {
      // 如果没有下一页数据，隐藏加载更多按钮
      console.log('No more data');
      return;
    }
    // 将新获取的数据与已有的数据拼接起来
    customers.value = customers.value.concat(newData);
    afterKey.value = response.data.after_key;
    console.log(afterKey.value);
  } catch (error) {
    // console.error('Request failed:', error);
  }
}

// 页面加载时，不带搜索词调用 submit 获取所有数据
onMounted(() => {
  submit();
});



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