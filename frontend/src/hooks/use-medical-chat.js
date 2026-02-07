import * as React from 'react'
import { useAppStore } from '@/store/useAppStore'
import { useAuth } from '@/auth/AuthProvider'

// Consolidated mock response generator
const generateMockResponse = (role) => {
    const isDoctor = role === 'doctor'

    const reasoning = `${isDoctor ? 'Analyzing clinical query' : 'Understanding your concern'}...
→ Retrieving relevant information
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
- This is a common concern that many people experience
- Lifestyle factors often play an important role
- Professional evaluation can provide personalized guidance

**General Recommendations:**
- Stay well hydrated
- Maintain regular sleep patterns
- Consider scheduling a check-up if symptoms persist

**When to seek care:** If symptoms worsen or persist beyond a few days.

*This is general information. Please consult a healthcare provider for personalized advice.*`

    return {
        reasoning,
        content: isDoctor ? doctorContent : patientContent,
        confidence: isDoctor ? 92 : 85,
        citations: isDoctor ? [{ id: 1, source: "Clinical Guidelines", page: 23 }] : []
    }
}

export function useMedicalChat() {
    const { setInteractionMode, interactionMode } = useAppStore()
    const { token, isOffline, user } = useAuth()

    const [messages, setMessages] = React.useState([])
    const [isLoading, setIsLoading] = React.useState(false)

    const userRole = user?.role || 'patient'

    const sendMessage = React.useCallback(async (text, file) => {
        if (!text && !file) return

        // Add user message
        const userMsg = { id: Date.now(), role: 'user', content: text, file: file ? { name: file.name } : null }
        setMessages(prev => [...prev, userMsg])

        if (interactionMode !== 'chat') setInteractionMode('chat')

        setIsLoading(true)
        const aiMsgId = Date.now() + 1

        // Add placeholder
        setMessages(prev => [...prev, { id: aiMsgId, role: 'ai', content: '', reasoning: '', confidence: 0, citations: [], isLoading: true }])

        // Use mock or real API
        if (isOffline || !token) {
            await simulateResponse(aiMsgId, userRole)
        } else {
            await fetchResponse(text, file, aiMsgId, userRole)
        }

        setIsLoading(false)
    }, [interactionMode, isOffline, token, userRole, setInteractionMode])

    const simulateResponse = async (aiMsgId, role) => {
        const mock = generateMockResponse(role)

        // Show reasoning
        setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, reasoning: mock.reasoning } : m))
        await new Promise(r => setTimeout(r, 600))

        // Stream content
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

    const fetchResponse = async (text, file, aiMsgId, role) => {
        try {
            const formData = new FormData()
            formData.append("query", text)
            formData.append("role", role)
            if (file) formData.append("file", file)

            const res = await fetch("http://localhost:8000/api/v1/chat/", {
                method: "POST",
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData,
            })

            if (!res.ok) throw new Error("API error")

            const reader = res.body.getReader()
            const decoder = new TextDecoder()
            let content = ""

            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                content += decoder.decode(value)
                setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content, isLoading: false } : m))
            }
        } catch {
            await simulateResponse(aiMsgId, role)
        }
    }

    return { messages, isLoading, sendMessage, userRole }
}
