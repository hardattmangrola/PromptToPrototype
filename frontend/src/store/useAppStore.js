import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Generate unique ID
const generateId = () => `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

export const useAppStore = create(
    persist(
        (set, get) => ({
            // ==================== UI ====================
            isSidebarOpen: false,
            toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),

            // ==================== Theme ====================
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

            // ==================== Settings ====================
            settingsOpen: false,
            toggleSettings: () => set((s) => ({ settingsOpen: !s.settingsOpen })),

            // ==================== Chats ====================
            chats: [],
            activeChatId: null,

            createChat: (isIncognito = false) => {
                const id = generateId()
                const newChat = {
                    id,
                    title: isIncognito ? 'Incognito Chat' : 'New Chat',
                    messages: [],
                    isIncognito,
                    createdAt: Date.now(),
                    patientContext: null,
                }
                set((s) => ({
                    chats: isIncognito ? s.chats : [newChat, ...s.chats],
                    activeChatId: id,
                    interactionMode: 'landing',
                    // Store incognito chat separately (not persisted)
                    incognitoChat: isIncognito ? newChat : s.incognitoChat,
                }))
                return id
            },

            deleteChat: (id) => set((s) => ({
                chats: s.chats.filter(c => c.id !== id),
                activeChatId: s.activeChatId === id ? null : s.activeChatId,
                interactionMode: s.activeChatId === id ? 'landing' : s.interactionMode,
            })),

            setActiveChat: (id) => {
                const state = get()
                const chat = state.chats.find(c => c.id === id) || state.incognitoChat
                if (chat) {
                    set({
                        activeChatId: id,
                        interactionMode: chat.messages.length > 0 ? 'chat' : 'landing',
                    })
                }
            },

            updateChatTitle: (id, title) => set((s) => ({
                chats: s.chats.map(c => c.id === id ? { ...c, title } : c),
            })),

            updateChatMessages: (id, messages) => set((s) => {
                // Check if it's incognito
                if (s.incognitoChat?.id === id) {
                    return { incognitoChat: { ...s.incognitoChat, messages } }
                }
                // Auto-generate title from first message
                const chat = s.chats.find(c => c.id === id)
                const shouldUpdateTitle = chat && chat.title === 'New Chat' && messages.length > 0
                const firstUserMsg = messages.find(m => m.role === 'user')
                const newTitle = shouldUpdateTitle && firstUserMsg
                    ? firstUserMsg.content.slice(0, 40) + (firstUserMsg.content.length > 40 ? '...' : '')
                    : chat?.title

                return {
                    chats: s.chats.map(c => c.id === id
                        ? { ...c, messages, title: newTitle || c.title }
                        : c
                    ),
                }
            }),

            setPatientContext: (id, context) => set((s) => ({
                chats: s.chats.map(c => c.id === id ? { ...c, patientContext: context } : c),
            })),

            clearAllChats: () => set({ chats: [], activeChatId: null, incognitoChat: null, interactionMode: 'landing' }),

            // Incognito (not persisted)
            incognitoChat: null,

            leaveIncognito: () => set({
                incognitoChat: null,
                activeChatId: null,
                interactionMode: 'landing',
            }),

            getActiveChat: () => {
                const state = get()
                if (state.incognitoChat?.id === state.activeChatId) return state.incognitoChat
                return state.chats.find(c => c.id === state.activeChatId) || null
            },

            // ==================== Interaction ====================
            interactionMode: 'landing', // 'landing' | 'chat'
            setInteractionMode: (mode) => set({ interactionMode: mode }),

            // ==================== PDF / Citations ====================
            activeCitation: null,
            setActiveCitation: (c) => set({ activeCitation: c }),
            closePDF: () => set({ activeCitation: null }),

            // ==================== Uploaded Document ====================
            uploadedDocument: null,
            setUploadedDocument: (doc) => set({ uploadedDocument: doc }),
        }),
        {
            name: 'clinical-ai-storage',
            partialize: (state) => ({
                chats: state.chats,
                isDarkMode: state.isDarkMode,
            }),
        }
    )
)
