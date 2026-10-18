import Vue from 'vue'
import App from './App.vue'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

Vue.config.productionTip = false
Vue.use(ElementUI)

// 全局事件总线，用于组件间联动与参数传递
Vue.prototype.$bus = new Vue()

new Vue({
  render: h => h(App),
}).$mount('#app')
