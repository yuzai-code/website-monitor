// FilterDisplay.vue

<template>
  <!-- Your component template -->
</template>

<script>
export default {
  // Your component logic
};

// 全局日期时间过滤器
Vue.filter('datetimeFilter', function (value) {
  if (value) {
    // 使用 JavaScript 内置的 Date 对象来解析ISO格式的时间字符串
    const date = new Date(value);
    // 使用 Date 对象的方法来生成常规的日期时间格式
    const formattedDate = date.toLocaleString(); // 根据本地时间格式生成日期时间字符串
    return formattedDate;
  }
});
</script>
