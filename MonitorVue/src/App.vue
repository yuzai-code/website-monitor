<template>
  <div class="flex-container">
    <div class="sidebar" v-if="visible">
      <div class="flex flex-column h-full">
        <div class="flex align-items-center justify-content-between px-4 pt-3 flex-shrink-0">
          <span class="inline-flex align-items-center gap-2">
            <svg width="35" height="40" viewBox="0 0 35 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="..." fill="var(--primary-color-color)" />
              <path d="..." fill="var(--text-color)" />
            </svg>
            <span class="font-semibold text-2xl text-primary">Website Monitor</span>
          </span>
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

<script setup>
import { ref } from 'vue'

const visible = ref(false) // State to control the visibility of the sidebar
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
