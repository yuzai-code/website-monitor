import axios, { AxiosRequestConfig, AxiosInstance, AxiosResponse } from 'axios'

const axiosInstance: AxiosInstance = axios.create({
  baseURL: 'https://127.0.0.1/',
  timeout: 5000
})

// 添加请求拦截器
axiosInstance.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 在发送请求之前做些什么
    // 检查当前请求的URL，判断是否是登录或注册请求
    if (!config.url?.endsWith('/login') && !config.url?.endsWith('/register')) {
      // 假设你的Token存储在localStorage中
      const token = localStorage.getItem('authToken')
      if (token) {
        // 如果 token 存在且请求不是登录或注册，为请求头添加 Authorization
        config.headers['Authorization'] = `Token ${token}`
      }
    }
    return config
  },
  (error: any) => {
    // 处理请求错误
    return Promise.reject(error)
  }
)

// 添加响应拦截器
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    // 对响应数据做点什么
    return response
  },
  (error: any) => {
    // 处理响应错误
    return Promise.reject(error)
  }
)

export default axiosInstance
