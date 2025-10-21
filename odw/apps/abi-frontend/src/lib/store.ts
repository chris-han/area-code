import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { WorkflowStatus, InfrastructureService } from '@/types'

interface AppState {
  // UI State
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  
  // System Health
  systemHealth: {
    overall: 'healthy' | 'degraded' | 'unhealthy'
    services: InfrastructureService[]
    lastCheck: Date | null
  }
  setSystemHealth: (health: Partial<AppState['systemHealth']>) => void
  
  // Active Workflows
  activeWorkflows: WorkflowStatus[]
  setActiveWorkflows: (workflows: WorkflowStatus[]) => void
  updateWorkflow: (id: string, updates: Partial<WorkflowStatus>) => void
  
  // Notifications
  notifications: Array<{
    id: string
    type: 'info' | 'success' | 'warning' | 'error'
    title: string
    message: string
    timestamp: Date
    read: boolean
  }>
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void
  markNotificationRead: (id: string) => void
  clearNotifications: () => void
}

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // UI State
      sidebarOpen: false,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      // System Health
      systemHealth: {
        overall: 'healthy',
        services: [],
        lastCheck: null,
      },
      setSystemHealth: (health) =>
        set((state) => ({
          systemHealth: { ...state.systemHealth, ...health },
        })),
      
      // Active Workflows
      activeWorkflows: [],
      setActiveWorkflows: (workflows) => set({ activeWorkflows: workflows }),
      updateWorkflow: (id, updates) =>
        set((state) => ({
          activeWorkflows: state.activeWorkflows.map((workflow) =>
            workflow.id === id ? { ...workflow, ...updates } : workflow
          ),
        })),
      
      // Notifications
      notifications: [],
      addNotification: (notification) =>
        set((state) => ({
          notifications: [
            {
              ...notification,
              id: Math.random().toString(36).substr(2, 9),
              timestamp: new Date(),
              read: false,
            },
            ...state.notifications,
          ],
        })),
      markNotificationRead: (id) =>
        set((state) => ({
          notifications: state.notifications.map((notification) =>
            notification.id === id ? { ...notification, read: true } : notification
          ),
        })),
      clearNotifications: () => set({ notifications: [] }),
    }),
    {
      name: 'abi-app-store',
    }
  )
)