// store/filterStore.ts
import { defineStore } from 'pinia'

export const useFilterStore = defineStore('filter', {
  state: () => ({
    selectedDate: new Date(),
    ipsData: { ips_all: [], ips_min: [], ips_hour: [], ips_day: [] }
  }),
  actions: {
    setDate(date: Date) {
      this.selectedDate = date
    },
    setIpsData(data: any) {
      this.ipsData = data
    }
  }
  //   persist: {
  //     enabled: true, // 启用持久化
  //     strategies: [
  //       {
  //         key: 'filter',
  //         storage: localStorage
  //       }
  //     ]
  //   }
})
