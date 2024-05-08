// store/filterStore.ts
import { defineStore } from 'pinia'

export const useFilterStore = defineStore('filter', {
  state: () => ({
    selectedDate: new Date(),
    ipsData: { ips_all: [], ips_min: [], ips_hour: [], ips_day: [] },
    websiteDate: new Date(),
    websiteList: [],
    afterKey: '',
    sortField: 'google_bot',
    sortOrder: -1 // 1: 升序, -1: 降序
  }),
  actions: {
    setDate(date: Date) {
      this.selectedDate = date
    },
    setIpsData(data: any) {
      this.ipsData = data
    },
    setWebsiteDate(date: Date) {
      this.websiteDate = date
    },
    setWebsiteList(data: any, key: string) {
      ;(this.websiteList = data), (this.afterKey = key)
    },
    setSort(field, order) {
      this.sortField = field
      this.sortOrder = order
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
