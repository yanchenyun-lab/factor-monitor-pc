<template>
  <div id="app">
    <StageLegend />
  </div>
</template>

<script>
/**
 * @file App.vue
 * @description 前端根组件容器，直接挂载业务核心主视图 StageLegend
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
#app {
  width: 100%;
  min-height: 100vh;
}
</style>
