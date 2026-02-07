import { create } from 'zustand'

export const useAppStore = create((set) => ({
    // UI
    isSidebarOpen: false,
    toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),

    // Theme
    isDarkMode: (() => {
        if (typeof window === 'undefined') return false
        const saved = localStorage.getItem('theme')
        if (saved) return saved === 'dark'
        return window.matchMedia('(prefers-color-scheme: dark)').matches
    })(),
    toggleDarkMode: () => set((s) => {
        const newMode = !s.isDarkMode
        document.documentElement.classList.toggle('dark', newMode)
        localStorage.setItem('theme', newMode ? 'dark' : 'light')
        return { isDarkMode: newMode }
    }),

    // Interaction
    interactionMode: 'landing', // 'landing' | 'chat'
    setInteractionMode: (mode) => set({ interactionMode: mode }),

    // PDF / Citations
    activeCitation: null,
    setActiveCitation: (c) => set({ activeCitation: c }),

    // Uploaded Document
    uploadedDocument: null, // { upload_id, namespace, filename, chunk_count }
    setUploadedDocument: (doc) => set({ uploadedDocument: doc }),
}))
