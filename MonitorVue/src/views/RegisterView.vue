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
        </form>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';

const username = ref('');
const password = ref('');

async function register() {
    try {
        const response = await axios.post('http://127.0.0.1:8000/register/', {
            username: username.value,
            password: password.value,
        });
        console.log('Registration successful', response.data);
        // 处理成功逻辑，例如跳转页面
    } catch (error) {
        console.error('Registration failed', error.response.data);
        // 处理错误，显示错误信息
    }
}

</script>
