<template>
    <button @click="logout">退出登录</button>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

function logout() {
    // 清除localStorage中的认证令牌
    localStorage.removeItem('authToken');

    // 可选：清除其他存储的用户信息

    // 重定向到登录页面或首页
    router.push({ name: 'Login' });
}
</script>