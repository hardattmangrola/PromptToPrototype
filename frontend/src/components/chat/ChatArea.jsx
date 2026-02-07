import * as React from "react"
import { motion } from "framer-motion"
import { MessageBubble } from "./MessageBubble"
import { MessageSquare } from "lucide-react"

/**
 * ChatArea Component
 * Scrollable message list with auto-scroll on new messages.
 */
export function ChatArea({ messages = [], isLoading }) {
    const scrollRef = React.useRef(null)

    // Auto-scroll to bottom on new messages
    React.useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: "smooth"
            })
        }
    }, [messages])

    if (messages.length === 0) {
        return null // HeroSearch handles the landing state
    }

    return (
        <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto px-4 py-6 pb-32 no-scrollbar"
        >
            <div className="max-w-4xl mx-auto space-y-6">
                {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                ))}
            </div>
        </div>
    )
}
