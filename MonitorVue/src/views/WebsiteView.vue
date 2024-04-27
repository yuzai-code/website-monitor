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
  console.log('Last page reached');
  // 用于加载下一页数据
  submit();
};

const submit = async () => {
  console.log('Sending request with afterKey:', afterKey.value);
  try {
    const response = await axiosInstance.get('api/website_list/', {
      params: {
        after_key: afterKey.value,
        search_text: value.value
      }
    })
    console.log('Response:', response.data);
    // 将后端分传递过来的数据与前面的数据加起来传递到 customers 中
    if (afterKey.value) {
      customers.value = [...customers.value, ...response.data.website_list];
    } else {
      customers.value = response.data.website_list;
    }

    afterKey.value = response.data.after_key;
    console.log('Updated afterKey:', afterKey.value);
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