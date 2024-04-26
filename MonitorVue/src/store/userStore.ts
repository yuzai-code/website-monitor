import axiosInstance from '@/axiosConfig'
import { UserProfile } from '@/types/userProfile'
import { defineStore } from 'pinia'

export const useUserStore = defineStore('userStore', {
  state: (): { userProfile: UserProfile | null; isLoggedIn: boolean } => ({
    userProfile: null, // 用户资料
    isLoggedIn: false // 登录状态
  }),
  actions: {
    setUserProfile(profile: UserProfile) {
      this.userProfile = profile
      this.isLoggedIn = true // 用户已登录
    },
    logout() {
      this.userProfile = null // 清除用户信息
      this.isLoggedIn = false // 标记用户未登录
    },
    login() {
      this.isLoggedIn = true // 标记用户已登录
    },
    async fetchUserProfile() {
      try {
        const response = await axiosInstance.get<UserProfile>('/api/user_settings')
        this.setUserProfile(response.data)
      } catch (error) {
        console.error('Failed to fetch user profile:', error)
      }
    }
  },
  getters: {
    // 可以保留原来的 isLoggedIn 的 getter，但不要试图为其赋值
    userProfileData(): UserProfile | null {
      return this.userProfile
    }
  }
})
