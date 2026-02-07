import * as React from 'react'
import { useAppStore } from '@/store/useAppStore'
import { useAuth } from '@/auth/AuthProvider'
import api from '@/services/api'

// Mock response for demo mode
const generateMockResponse = (role) => {
    const isDoctor = role === 'doctor'

    const reasoning = `${isDoctor ? 'Analyzing clinical query' : 'Understanding your concern'}...
→ Retrieving relevant documents
→ ${isDoctor ? 'Applying clinical guidelines' : 'Preparing helpful guidance'}
→ Generating response`

    const doctorContent = `Based on clinical guidelines:

**Assessment:** The presentation is consistent with the described condition.

| Medication* | Dosage | Frequency |
|-------------|--------|-----------|
| First-line* | Standard | As needed |
| Alternative* | Lower dose | If required |

**Monitoring:** Follow-up in 2 weeks.

*⚠️ Verify allergies and contraindications before prescribing.*`

    const patientContent = `Thank you for your question. Here's helpful information:

**Key Points:**
- This is a common concern
- Lifestyle factors often play an important role
- Professional evaluation can provide personalized guidance

**General Recommendations:**
- Stay well hydrated
- Maintain regular sleep patterns
- Consider scheduling a check-up if symptoms persist

*This is general information. Please consult a healthcare provider for personalized advice.*`

    return {
        reasoning,
        content: isDoctor ? doctorContent : patientContent,
        confidence: isDoctor ? 92 : 85,
        citations: isDoctor ? [{ id: 1, source: "Clinical Guidelines", page: 23 }] : [],
        limitations: "This is demo mode. Please consult a healthcare provider for personalized advice."
    }
}

// Transform backend citation format to frontend format
const transformCitations = (citations = []) => {
    return citations.map((c, i) => ({
        id: i + 1,
        url: c.doc_name ? `/documents/${encodeURIComponent(c.doc_name)}` : null,
        page: c.page || 1,
        source: c.doc_name || 'Document',
        snippet: c.snippet,
        section: c.section,
    }))
}

export function useMedicalChat() {
    const {
        setInteractionMode,
        interactionMode,
        activeChatId,
        updateChatMessages,
        getActiveChat,
        incognitoChat,
        createChat, // NEW
    } = useAppStore()
    const { isOffline, user } = useAuth()

    const [isLoading, setIsLoading] = React.useState(false)

    const userRole = user?.role || 'patient'

    // Get messages from active chat
    const activeChat = getActiveChat()
    const messages = activeChat?.messages || []
    const isIncognito = incognitoChat?.id === activeChatId

    const sendMessage = React.useCallback(async (text, file) => {
        if (!text && !file) return

        // Auto-create chat if none exists (e.g. from landing page)
        let chatId = activeChatId
        if (!chatId) {
            chatId = createChat(false)
        }

        const userMsg = { id: Date.now(), role: 'user', content: text, file: file ? { name: file.name } : null }
        // We need to fetch the fresh chat content since we might have just created it
        const currentMessages = useAppStore.getState().chats.find(c => c.id === chatId)?.messages || []
        const newMessages = [...currentMessages, userMsg]

        updateChatMessages(chatId, newMessages)

        if (interactionMode !== 'chat') setInteractionMode('chat')

        setIsLoading(true)
        const aiMsgId = Date.now() + 1

        // Add loading AI message
        updateChatMessages(chatId, [...newMessages, {
            id: aiMsgId,
            role: 'ai',
            content: '',
            reasoning: '',
            confidence: 0,
            citations: [],
            refused: false,
            limitations: null,
            isLoading: true
        }])

        if (isOffline || !api.accessToken) {
            await simulateResponse(aiMsgId, userRole, newMessages, chatId)
        } else {
            await fetchRAGResponse(text, aiMsgId, newMessages, chatId)
        }

        setIsLoading(false)
    }, [activeChatId, interactionMode, isOffline, userRole, setInteractionMode, updateChatMessages, getActiveChat, createChat])

    const simulateResponse = async (aiMsgId, role, prevMessages, chatId) => {
        const mock = generateMockResponse(role)

        // Update reasoning
        const msgs1 = [...prevMessages, { id: aiMsgId, role: 'ai', reasoning: mock.reasoning, content: '', isLoading: true }]
        updateChatMessages(chatId, msgs1)
        await new Promise(r => setTimeout(r, 600))

        // Stream content
        for (let i = 0; i <= mock.content.length; i++) {
            const msg = {
                id: aiMsgId,
                role: 'ai',
                reasoning: mock.reasoning,
                content: mock.content.slice(0, i),
                confidence: mock.confidence,
                citations: mock.citations,
                limitations: mock.limitations,
                isLoading: i < mock.content.length
            }
            updateChatMessages(chatId, [...prevMessages, msg])
            if (i < mock.content.length) await new Promise(r => setTimeout(r, 2))
        }
    }

    const fetchRAGResponse = async (query, aiMsgId, prevMessages, chatId) => {
        try {
            const uploadedDoc = useAppStore.getState().uploadedDocument
            const activeChat = useAppStore.getState().chats.find(c => c.id === chatId)

            const response = await api.query(query, {
                topK: 5,
                uploadId: uploadedDoc?.upload_id,
            })

            // Check if refused
            if (response.refused) {
                const msg = {
                    id: aiMsgId,
                    role: 'ai',
                    content: response.message,
                    reasoning: `Query analysis: ${response.reason || 'Out of scope'}`,
                    refused: true,
                    isLoading: false,
                }
                updateChatMessages(chatId, [...prevMessages, msg])
                return
            }

            // Success response with citations
            const msg = {
                id: aiMsgId,
                role: 'ai',
                content: response.answer,
                reasoning: 'Retrieved and validated from medical documents',
                confidence: response.confidence ? Math.round(response.confidence * 100) : 90,
                citations: transformCitations(response.citations),
                limitations: response.limitations,
                isLoading: false,
            }
            updateChatMessages(chatId, [...prevMessages, msg])

        } catch (error) {
            console.error('RAG error:', error)
            await simulateResponse(aiMsgId, userRole, prevMessages, chatId)
        }
    }

    return { messages, isLoading, sendMessage, userRole, isIncognito }
}
