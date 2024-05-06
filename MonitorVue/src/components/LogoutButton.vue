<template>
    <Button @click="logout">退出登录</Button>
</template>

<script setup lang="ts">
import { useUserStore } from '@/store/userStore'; // 引入用户信息store
import Button from 'primevue/button';
import { useRouter } from 'vue-router';

const router = useRouter();

const userStore = useUserStore(); // 获取用户信息store
function logout() {
    // 清除localStorage中的认证令牌
    localStorage.removeItem('authToken');

    userStore.logout(); // 调用用户信息store中的logout方法
    location.reload();
    router.push('/login');
}
</script>