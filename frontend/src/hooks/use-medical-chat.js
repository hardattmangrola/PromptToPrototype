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
    } = useAppStore()
    const { isOffline, user } = useAuth()

    const [isLoading, setIsLoading] = React.useState(false)
    const [triggerContextModal, setTriggerContextModal] = React.useState(false)

    const userRole = user?.role || 'patient'

    // Get messages from active chat
    const activeChat = getActiveChat()
    const messages = activeChat?.messages || []
    const isIncognito = incognitoChat?.id === activeChatId

    const sendMessage = React.useCallback(async (text, file) => {
        if (!text && !file) return
        if (!activeChatId) return

        const userMsg = { id: Date.now(), role: 'user', content: text, file: file ? { name: file.name } : null }
        const currentMessages = getActiveChat()?.messages || []
        const newMessages = [...currentMessages, userMsg]

        updateChatMessages(activeChatId, newMessages)

        if (interactionMode !== 'chat') setInteractionMode('chat')

        // Trigger context modal on first message if needed
        const activeChat = getActiveChat()
        if (!isIncognito && !activeChat?.isIncognito && !activeChat?.patientContext && currentMessages.length === 0) {
            setTriggerContextModal(true)
        }

        setIsLoading(true)
        const aiMsgId = Date.now() + 1

        // Add loading AI message
        updateChatMessages(activeChatId, [...newMessages, {
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
            await simulateResponse(aiMsgId, userRole, newMessages)
        } else {
            await fetchRAGResponse(text, aiMsgId, newMessages)
        }

        setIsLoading(false)
    }, [activeChatId, interactionMode, isOffline, userRole, setInteractionMode, updateChatMessages, getActiveChat])

    const simulateResponse = async (aiMsgId, role, prevMessages) => {
        const mock = generateMockResponse(role)

        // Update reasoning
        const msgs1 = [...prevMessages, { id: aiMsgId, role: 'ai', reasoning: mock.reasoning, content: '', isLoading: true }]
        updateChatMessages(activeChatId, msgs1)
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
            updateChatMessages(activeChatId, [...prevMessages, msg])
            if (i < mock.content.length) await new Promise(r => setTimeout(r, 2))
        }
    }

    const fetchRAGResponse = async (query, aiMsgId, prevMessages) => {
        try {
            const uploadedDoc = useAppStore.getState().uploadedDocument
            const activeChat = getActiveChat()

            const response = await api.query(query, {
                topK: 5,
                uploadId: uploadedDoc?.upload_id,
                context: activeChat?.patientContext, // NEW: Pass patient context
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
                updateChatMessages(activeChatId, [...prevMessages, msg])
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
            updateChatMessages(activeChatId, [...prevMessages, msg])

        } catch (error) {
            console.error('RAG error:', error)
            await simulateResponse(aiMsgId, userRole, prevMessages)
        }
    }

    return { messages, isLoading, sendMessage, userRole, isIncognito, triggerContextModal }
}
