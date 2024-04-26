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
        <router-link to="/register" class="register-button" rounded>
            Register
        </router-link>

    </div>

</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import { useUserStore } from '@/store/userStore'; // 引入用户信息store
import { useToast } from 'primevue/usetoast';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

// 使用ref创建响应式引用
const username = ref('');
const password = ref('');
const toast = useToast();
const router = useRouter(); // 使用useRouter获取路由实例
const userStore = useUserStore(); // 获取用户信息store

async function login() {
    try {
        const response = await axiosInstance.post('login/', { // 注意这里使用了axiosInstance
            username: username.value,
            password: password.value,
        });

        localStorage.setItem('authToken', response.data.token);  // 将获取的认证令牌保存到localStorage中
        toast.add({ severity: 'success', summary: '登录成功', detail: '您已成功登录' });
        userStore.login(); // 调用store中的login方法
        await userStore.fetchUserProfile(); // 登录成功后获取用户信息
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
