import type {
  AxiosInstance,
  AxiosRequestHeaders,
  AxiosResponse,
  InternalAxiosRequestConfig
} from 'axios'
import axios from 'axios'

const axiosInstance: AxiosInstance = axios.create({
  baseURL: 'http://192.168.0.163:8001/',
  timeout: 5001
})

// 请求拦截器
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 使用类型断言确保 config.headers 的类型为 AxiosRequestHeaders
    config.headers = config.headers as AxiosRequestHeaders

    // 检查当前请求的 URL，判断是否是登录或注册请求
    if (!config.url?.endsWith('/login') && !config.url?.endsWith('/register/')) {
      // 假设你的 Token 存储在 localStorage 中
      const token = localStorage.getItem('authToken')
      if (token) {
        // 如果 token 存在且请求不是登录或注册，为请求头添加 Authorization
        config.headers['Authorization'] = `Token ${token}`
      }
    }

    // 返回更新后的 config 对象
    return config
  },
  (error) => {
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
  (error) => {
    // 处理响应错误
    return Promise.reject(error)
  }
)

export default axiosInstance
