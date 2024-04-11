<template>
    <div>
        <h2>Register</h2>
        <form @submit.prevent="register">
            <div>
                <label for="username">Username:</label>
                <input id="username" v-model="username" type="text" />
            </div>
            <div>
                <label for="password">Password:</label>
                <input id="password" v-model="password" type="password" />
            </div>
            <button type="submit">Register</button>
            <!-- <Toast /> -->
        </form>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axiosInstance from '@/axiosConfig'
import { useToast } from 'primevue/usetoast';

const username = ref('');
const password = ref('');
const toast = useToast();

async function register() {
    try {
        const response = await axiosInstance.post('register/', {
            username: username.value,
            password: password.value,
        });
        console.log('Registration successful', response.data);
        console.log('toast:', toast)
        // 处理成功逻辑，例如跳转页面
        toast.add({ severity: 'success', summary: '注册成功', detail: '您已成功注册' });
    } catch (error) {
        console.error('Registration failed', error.response.data);
        // 处理错误，显示错误信息
        toast.add({ severity: 'error', summary: '注册失败', detail: '注册信息错误或服务器问题' });
    }
}

</script>
