import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
// primevue
import 'primeflex/primeflex.css'
import 'primeicons/primeicons.css'
import PrimeVue from 'primevue/config'
import 'primevue/resources/primevue.min.css' /* Deprecated */
import 'primevue/resources/themes/aura-light-green/theme.css'
import Ripple from 'primevue/ripple'
// import './style.css'
// import './flags.css'

import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import AutoComplete from 'primevue/autocomplete'
import Avatar from 'primevue/avatar'
import AvatarGroup from 'primevue/avatargroup'
import Button from 'primevue/button'
import Calendar from 'primevue/calendar'
import Card from 'primevue/card'
import Column from 'primevue/column'
import ColumnGroup from 'primevue/columngroup' // optional
import ConfirmationService from 'primevue/confirmationservice'
import DataTable from 'primevue/datatable'
import DialogService from 'primevue/dialogservice'
import FileUpload from 'primevue/fileupload'
import InputText from 'primevue/inputtext'
import Row from 'primevue/row' // optional
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
// main.js 或 main.ts
import axios from 'axios'
import { useUserStore } from './store/userStore'

const pinia = createPinia()
const app = createApp(App)

app.use(PrimeVue, { ripple: true })
app.use(ConfirmationService)
app.use(ToastService)
app.use(DialogService)
app.use(router)
// app.use(createPinia())
app.use(pinia)

const userStore = useUserStore()
// Token存储在localStorage中
const token = localStorage.getItem('authToken')
if (token) {
  // 设置用户的登陆状态
  userStore.login()
  userStore.fetchUserProfile()
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
}
// app.component('Button', Button)
// eslint-disable-next-line vue/multi-word-component-names
app.component('Toast', Toast)
app.component('Accordion', Accordion)
app.component('ColumnGroup', ColumnGroup)
app.component('Row', Row)
app.component('AccordionTab', AccordionTab)
app.component('AutoComplete', AutoComplete)
// eslint-disable-next-line vue/multi-word-component-names
app.component('Avatar', Avatar)
app.component('AvatarGroup', AvatarGroup)

// eslint-disable-next-line vue/multi-word-component-names
app.component('Button', Button)
app.component('Calendar', Calendar)
app.component('Card', Card)
app.component('Column', Column)
app.component('DataTable', DataTable)
app.component('FileUpload', FileUpload)
app.component('InputText', InputText)

app.directive('ripple', Ripple)

app.mount('#app')
