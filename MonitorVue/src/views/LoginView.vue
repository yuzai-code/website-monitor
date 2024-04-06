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

// 使用ref创建响应式引用
const username = ref('');
const password = ref('');

const router = useRouter(); // 使用useRouter获取路由实例

async function login() {
    const response = await fetch('http://127.0.0.1:8000/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username.value, // 访问ref值需要使用.value
            password: password.value,
        }),
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.token);
        console.log('Login successful');
        router.push({ name: 'Home' }); // 使用路由实例进行导航
    } else {
        console.log('Login failed');
    }
}
</script>