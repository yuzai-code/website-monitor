<template>
  <div class="flex-container">
    <Toast />
    <div class="sidebar" v-if="visible">
      <div class="flex flex-column h-full">

        <div class="flex align-items-center justify-content-between px-4 pt-3 flex-shrink-0">

          <div>
            <span class="inline-flex align-items-center gap-2" @click="showUserProfile">
              <Avatar :label="getAvatarLabel(userProfile.user)" class="mr-2" size="large"
                style="background-color: #ece9fc; color: #2a1261" />
              <span class="font-semibold text-2xl text-primary">Monitor</span>
            </span>
            <UserProfile ref="userProfileRef" />
          </div>
        </div>
        <div class="overflow-y-auto">
          <ul class="list-none p-0 m-0 overflow-hidden">
            <li>
              <router-link to="/"
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-home mr-2"></i>
                <span class="font-medium">首页</span>
              </router-link>
            </li>
            <li>
              <router-link to="/website"
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-bookmark mr-2"></i>
                <span class="font-medium">网站列表</span>
              </router-link>
            </li>
            <li>

              <router-link to="/ip_list"
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-users mr-2"></i>
                <span class="font-medium">IP统计</span>
              </router-link>
            </li>
            <li>
              <router-link to="/spider"
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-comments mr-2"></i>
                <span class="font-medium">蜘蛛统计</span>
              </router-link>
            </li>
            <li>
              <a v-ripple
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-calendar mr-2"></i>
                <span class="font-medium">客户端统计</span>
              </a>
            </li>
            <li>
              <a v-ripple
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-cog mr-2"></i>
                <span class="font-medium">URL统计</span>
              </a>
            </li>
            <li>
              <router-link to="/total" class="flex align-items-center cursor-pointer p-3 border-round text-700
                hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-folder mr-2"></i>
                <span class="font-medium">汇总</span></router-link>
            </li>
            <li>
              <a v-ripple
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-chart-bar mr-2"></i>
                <span class="font-medium">Performance</span>
              </a>
            </li>
            <li>
              <a v-ripple
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-cog mr-2"></i>
                <span class="font-medium">Settings</span>
              </a>
            </li>
            <li>
              <LogoutButton />
            </li>
            <li>
              <router-link :to="{ name: 'Login' }"
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-cog mr-2"></i>
                <span class="font-medium">登录</span>
              </router-link>
            </li>
            <li>
              <router-link :to="{ name: 'Register' }"
                class="flex align-items-center cursor-pointer p-3 border-round text-700 hover:surface-100 transition-duration-150 transition-colors p-ripple">
                <i class="pi pi-cog mr-2"></i>
                <span class="font-medium">注册</span>
              </router-link>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <!-- Main Content -->
    <div class="main-content">
      <!-- Main content area -->
      <Button icon="pi pi-bars" @click="visible = !visible" class="toggle-button" />
      <!-- Toggle button to show/hide sidebar -->
      <!-- Your content goes here -->
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import LogoutButton from '@/components/LogoutButton.vue';
import UserProfile from '@/components/UserProfile.vue';
import { storeToRefs } from 'pinia';
import { useToast } from 'primevue/usetoast';
import { computed, ref } from 'vue';
import { useUserStore } from './store/userStore';


const visible = ref(false) // State to control the visibility of the sidebar
const isUserLoggedIn = computed(() => useUserStore().isLoggedIn);
const toast = useToast();
// 正确声明 ref
const userProfileRef = ref();
const userProfile = storeToRefs(useUserStore()).userProfile;


// 修改此处确保正确调用子组件方法
const showUserProfile = () => {
  if (!isUserLoggedIn.value) {
    // 如果用户未登录，不执行任何操作
    // console.log('用户未登录，无法显示用户个人资料');
    toast.add({
      severity: 'error',
      summary: '请先登录',
      detail: '请先登录后才能查看个人资料'
    });
    return;
  }


  // 用户已登录时才执行以下操作
  if (userProfileRef.value) {
    // 调用用户个人资料组件的显示方法
    userProfileRef.value.show();
  }
};



const getAvatarLabel = (username) => {
  // 返回用户名的首字母作为 Avatar 的 label
  return username.charAt(0).toUpperCase();
};

// onMounted(() => {
//   fetchData()
// })
</script>

<style scoped>
.flex-container {
  display: flex;
  /* Establishes a flex container */
  min-height: 100vh;
  /* Full height of the viewport */
}

.sidebar {
  width: 250px;
  /* Set the width of the sidebar */
  background: #f7f4f4;
  /* Example background color for the sidebar */
}

.main-content {
  flex-grow: 1;
  /* Allows the main content to take up the remaining space */
  padding: 20px;
  /* Add some padding */
  background-color: var(--surface-color);
  border-radius: 0.5rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.toggle-button {
  margin-bottom: 20px;
  /* Spacing for the toggle button */
  /* Style your toggle button as needed */
}
</style>
