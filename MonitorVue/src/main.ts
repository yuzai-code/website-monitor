import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
// primevue
import PrimeVue from 'primevue/config'
import 'primeflex/primeflex.css'
import 'primevue/resources/themes/aura-light-green/theme.css'
import 'primevue/resources/primevue.min.css' /* Deprecated */
import 'primeicons/primeicons.css'
// import './style.css'
// import './flags.css'

import AutoComplete from 'primevue/autocomplete'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import Avatar from 'primevue/avatar'
import AvatarGroup from 'primevue/avatargroup'
import Button from 'primevue/button'
import Calendar from 'primevue/calendar'
import Column from 'primevue/column'
import ConfirmationService from 'primevue/confirmationservice'
import DataTable from 'primevue/datatable'
import DialogService from 'primevue/dialogservice'
import ToastService from 'primevue/toastservice'
import FileUpload from 'primevue/fileupload';
import InputText from 'primevue/inputtext';


const app = createApp(App)

app.use(PrimeVue, { ripple: true })
app.use(ConfirmationService)
app.use(ToastService)
app.use(DialogService)
app.use(router)

// app.component('Button', Button)
// eslint-disable-next-line vue/multi-word-component-names
app.component('Accordion', Accordion)
app.component('AccordionTab', AccordionTab)
app.component('AutoComplete', AutoComplete)
// eslint-disable-next-line vue/multi-word-component-names
app.component('Avatar', Avatar)
app.component('AvatarGroup', AvatarGroup)
// eslint-disable-next-line vue/multi-word-component-names
// eslint-disable-next-line vue/multi-word-component-names
app.component('Button', Button)
app.component('Calendar', Calendar)
app.component('Column', Column)
app.component('DataTable', DataTable)
app.component('FileUpload', FileUpload)
app.component('InputText',InputText)

app.mount('#app')
