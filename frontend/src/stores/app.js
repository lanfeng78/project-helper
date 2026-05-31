import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const currentProjectId = ref(null)
  const currentReport = ref(null)
  const projects = ref([])

  function setProject(id) { currentProjectId.value = id }
  function setReport(report) { currentReport.value = report }
  function setProjects(list) { projects.value = list }

  return { currentProjectId, currentReport, projects, setProject, setReport, setProjects }
})
