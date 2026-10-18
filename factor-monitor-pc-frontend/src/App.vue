<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <h2>三因子宏观经济周期划分的风险预算资产配置模型</h2>
      </el-header>
      <el-main>
        <StageLegend />
      </el-main>
    </el-container>
  </div>
</template>

<script>
/**
 * @file App.vue
 * @description 前端根组件容器
 * 负责挂载核心主视图 StageLegend，全局时间筛选与多模块业务联动已完全由 StageLegend 内部独立自闭环管理。
 */
import StageLegend from './components/StageLegend.vue'

export default {
  name: 'App',
  components: {
    StageLegend
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #f5f7fa;
}
.el-header {
  background-color: #409EFF;
  color: white;
  line-height: 60px;
  text-align: center;
}
.app-header {
  display: flex;
  justify-content: center;
  align-items: center;
}
.el-header h2 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 1px;
}
</style>
