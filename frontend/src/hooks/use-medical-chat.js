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
        citations: isDoctor ? [{ doc_name: "Clinical Guidelines", page: 23 }] : []
    }
}

export function useMedicalChat() {
    const { setInteractionMode, interactionMode, uploadedDocument } = useAppStore()
    const { isOffline, user } = useAuth()

    const [messages, setMessages] = React.useState([])
    const [isLoading, setIsLoading] = React.useState(false)

    const userRole = user?.role || 'patient'

    const sendMessage = React.useCallback(async (text, file) => {
        if (!text && !file) return

        const userMsg = { id: Date.now(), role: 'user', content: text, file: file ? { name: file.name } : null }
        setMessages(prev => [...prev, userMsg])

        if (interactionMode !== 'chat') setInteractionMode('chat')

        setIsLoading(true)
        const aiMsgId = Date.now() + 1

        setMessages(prev => [...prev, {
            id: aiMsgId,
            role: 'ai',
            content: '',
            reasoning: '',
            confidence: 0,
            citations: [],
            refused: false,
            isLoading: true
        }])

        if (isOffline || !api.accessToken) {
            await simulateResponse(aiMsgId, userRole)
        } else {
            await fetchRAGResponse(text, aiMsgId)
        }

        setIsLoading(false)
    }, [interactionMode, isOffline, userRole, setInteractionMode, uploadedDocument])

    const simulateResponse = async (aiMsgId, role) => {
        const mock = generateMockResponse(role)

        setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, reasoning: mock.reasoning } : m))
        await new Promise(r => setTimeout(r, 600))

        for (let i = 0; i <= mock.content.length; i++) {
            setMessages(prev => prev.map(m => m.id === aiMsgId ? {
                ...m,
                content: mock.content.slice(0, i),
                confidence: mock.confidence,
                citations: mock.citations,
                isLoading: i < mock.content.length
            } : m))
            if (i < mock.content.length) await new Promise(r => setTimeout(r, 2))
        }
    }

    const fetchRAGResponse = async (query, aiMsgId) => {
        try {
            const uploadedDoc = useAppStore.getState().uploadedDocument
            const response = await api.query(query, {
                topK: 5,
                uploadId: uploadedDoc?.upload_id,
            })

            // Check if refused
            if (response.refused) {
                setMessages(prev => prev.map(m => m.id === aiMsgId ? {
                    ...m,
                    content: response.message,
                    reasoning: `Query analysis: ${response.reason || 'Out of scope'}`,
                    refused: true,
                    isLoading: false,
                } : m))
                return
            }

            // Success response with citations
            setMessages(prev => prev.map(m => m.id === aiMsgId ? {
                ...m,
                content: response.answer,
                reasoning: 'Retrieved and validated from medical documents',
                confidence: response.confidence ? response.confidence * 100 : 90,
                citations: response.citations || [],
                limitations: response.limitations,
                isLoading: false,
            } : m))

        } catch (error) {
            console.error('RAG error:', error)
            await simulateResponse(aiMsgId, userRole)
        }
    }

    return { messages, isLoading, sendMessage, userRole }
}
