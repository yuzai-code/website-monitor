// utils.js
export function bytesToGB(bytes) {
  return (bytes / 1024 ** 3).toFixed(2) // 保留两位小数
}
