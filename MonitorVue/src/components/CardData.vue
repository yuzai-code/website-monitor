<template>
  <p>按日期统计总量</p>
  <div class="card-data" v-if="websiteData">

    <div class="data-item">
      <span class="label-card">访客量</span>
      <span class="value">{{ websiteData.visitor_totals }}</span>
    </div>
    <div class="data-item">
      <span class="label-card">IP数</span>
      <span class="value">{{ websiteData.ip_totals }}</span>
    </div>
    <div class="data-item">
      <span class="label-card">流量</span>
      <span class="value">{{ websiteData.data_transfer_totals }}</span>
    </div>
    <div class="data-item">
      <span class="label-card">请求</span>
      <span class="value">{{ websiteData.visit_totals }}</span>
    </div>
  </div>
  <div class="card-data" v-else>
    <span>暂无数据</span>
  </div>
</template>

<script setup lang="ts">
defineProps({
  websiteData: Object
})
</script>

<style scoped>
.card-data {
  display: flex;
  justify-content: space-around;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 20px;
  /* 控制网格间的间隙 */
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
}

.data-item {
  display: flex;
  flex-direction: column;
  /* 描述和数据垂直排列 */
  align-items: center;
  /* 居中对齐 */
}

.label-card,
.value {
  text-align: center;
  /* 确保文本居中对齐 */
  margin-bottom: 10px;
  /* 间距 */
}
</style>