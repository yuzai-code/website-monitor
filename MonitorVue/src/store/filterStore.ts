import { defineStore } from 'pinia'

export const useFilterStore = defineStore('filter', {
  state: () => ({
    selectedDate: new Date()
  }),
  actions: {
    setDate(date: Date) {
      this.selectedDate = date
    }
  },
  getters: {
    formattedDate: (state) => {
      return state.selectedDate.toISOString().slice(0, 10) // 只保留日期部分
    }
  },
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'filter',
        storage: localStorage
      }
    ]
  }
})
