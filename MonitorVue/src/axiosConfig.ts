import axios, { AxiosRequestConfig, AxiosInstance, AxiosResponse } from 'axios'

const axiosInstance: AxiosInstance = axios.create({
  baseURL: 'http://192.168.0.163:8001/',
  timeout: 5000
})

// 添加请求拦截器
axiosInstance.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // TypeScript 3.9+ 对象展开运算符可正确推断类型，不再需要明确断言
    const headers = config.headers || {}

    // 检查当前请求的URL，判断是否是登录或注册请求
    if (!config.url?.endsWith('/login') && !config.url?.endsWith('/register/')) {
      // 假设你的Token存储在localStorage中
      const token = localStorage.getItem('authToken')
      if (token) {
        // 如果 token 存在且请求不是登录或注册，为请求头添加 Authorization
        headers['Authorization'] = `Token ${token}`
      }
    }

    // 确保headers被正确设置回config对象
    config.headers = headers
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
