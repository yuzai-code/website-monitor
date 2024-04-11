<template>
    <div>
        <h2>Login</h2>
        <form @submit.prevent="login">
            <div>
                <label for="username">Username:</label>
                <input id="username" v-model="username" type="text" />
            </div>
            <div>
                <label for="password">Password:</label>
                <input id="password" v-model="password" type="password" />
            </div>
            <button type="submit">Login</button>
        </form>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axiosInstance from '@/axiosConfig'
import { useToast } from 'primevue/usetoast';

// 使用ref创建响应式引用
const username = ref('');
const password = ref('');
const toast = useToast();
const router = useRouter(); // 使用useRouter获取路由实例

async function login() {
    try {
        const response = await axiosInstance.post('login/', { // 注意这里使用了axiosInstance
            username: username.value,
            password: password.value,
        });

        localStorage.setItem('authToken', response.data.token);
        toast.add({ severity: 'success', summary: '登录成功', detail: '您已成功登录' });
        router.push({ name: 'Home' });
    } catch (error) {
        if (error.response && error.response.status === 400) {
            toast.add({ severity: 'error', summary: '登录失败', detail: '登陆账号密码错误' });
        } else {
            toast.add({ severity: 'error', summary: '登录失败', detail: '服务器错误' });
        }
    }
}
</script>