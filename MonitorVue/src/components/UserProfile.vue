<template>
    <Dialog v-model:visible="visible" modal header="编辑个人资料" :style="{ width: '30rem' }">
        <span class="p-text-secondary block mb-5">更新你的个人信息.</span>
        <div class="flex align-items-center gap-3 mb-3">
            <label for="user" class="font-semibold w-6rem">用户名</label>
            <InputText id="user" v-model="userProfile.user" class="flex-auto" autocomplete="off" />
        </div>
        <div class="flex align-items-center gap-3 mb-5">
            <label for="email" class="font-semibold w-6rem">nginx日志格式</label>
            <Textarea v-model="userProfile.nginx_log_format" rows="5" cols="30" />
        </div>
        <div class="flex justify-content-end gap-2">
            <Button type="button" label="取消" severity="secondary" @click="visible = false"></Button>
            <Button type="button" label="保存" @click="saveProfile"></Button>
        </div>
    </Dialog>
</template>

<script setup lang="ts">
import axiosInstance from '@/axiosConfig';
import { useUserStore } from '@/store/userStore'; // 引入用户信息store
import { storeToRefs } from 'pinia';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import { useToast } from 'primevue/usetoast';
import { computed, ref } from 'vue';



const visible = ref(false);
// const username = ref(props.initialUsername);
// const nginxLogFormat = ref(props.initialNginxLogFormat);
const toast = useToast();
const { userProfile } = storeToRefs(useUserStore());// 获取用户信息store

// console.log('1111', userProfile.value);
// 假设用户登录状态存储在userStore的isUserLoggedIn属性中
const isUserLoggedIn = computed(() => useUserStore().isLoggedIn);

// 定义需要暴露给外部的属性和方法
defineExpose({
    show() {
        visible.value = true;
    },
    hide() {
        visible.value = false;
    },
    emitUserProfile() {
        return userProfile.value;
    }
});

const saveProfile = async () => {
    if (!isUserLoggedIn.value) {
        // 如果用户未登录，在这里可以添加相应的提示或重定向到登录页面
        toast.add({
            severity: 'error',
            summary: '请先登录',
            detail: '请先登录后才能保存个人资料'
        });
        return;
    }


    // 保存用户信息
    const data = {
        username: userProfile.value.user,
        nginxLogFormat: userProfile.value.nginx_log_format
    };
    try {
        // 调用修改用户信息的接口
        const response = await axiosInstance.post('/api/user_settings/', data);
        if (response.status === 200) {
            // console.log('保存成功');
            toast.add({
                severity: 'success',
                summary: '保存成功',
                detail: '个人资料已更新'
            });
            // 保存成功后关闭对话框
            visible.value = false;
        } else {
            // console.error('保存失败');
            toast.add({
                severity: 'error',
                summary: '保存失败',
                detail: '个人资料更新失败，请重试'
            });
        }

    } catch (error) {
        // console.error('Failed to save user profile:', error);
        toast.add({
            severity: 'error',
            summary: '保存失败',
            detail: '个人资料更新失败，请重试'
        });
    }

}
</script>