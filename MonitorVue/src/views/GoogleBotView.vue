<template>
    <div>
        test
        {{ domain }}
    </div>
    
</template>
<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';



const route = useRoute();
const domain = route.params.domain;

// 页面加载时请求数据
onMounted(() => {
    fetchData();
});

// 向后端请求数据
const fetchData = async () => {
    try {
        const response = await axiosInstance.get(`/api/website_detail/googlebot/${domain}/`);
        console.log('Response:', response.data);
    } catch (error) {
        console.error('Request failed:', error);
    }
}



</script>
