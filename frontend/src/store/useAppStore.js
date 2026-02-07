import { create } from 'zustand'

export const useAppStore = create((set) => ({
    // UI State
    isSidebarOpen: false,
    userMode: 'doctor', // 'doctor' | 'patient'
    interactionMode: 'landing', // 'landing' | 'chat'
    isDarkMode: false,

    // PDF State
    activeCitation: null, // { url: string, page: number, highlight?: object }

    // Actions
    toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
    setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),
    setUserMode: (mode) => set({ userMode: mode }),
    setInteractionMode: (mode) => set({ interactionMode: mode }),
    setActiveCitation: (citation) => set({ activeCitation: citation }),
    closePDF: () => set({ activeCitation: null }),
    toggleDarkMode: () => set((state) => {
        const newMode = !state.isDarkMode
        if (newMode) {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
        return { isDarkMode: newMode }
    }),
}))
