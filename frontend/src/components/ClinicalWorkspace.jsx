import { Layout } from "@/components/layout/Layout"
import { HeroSearch } from "@/components/landing/HeroSearch"
import { ChatArea } from "@/components/chat/ChatArea"
import { PDFViewer } from "@/components/reference/PDFViewer"
import { useAppStore } from "@/store/useAppStore"
import { AnimatePresence, motion } from "framer-motion"
import { useIsMobile } from "@/hooks/use-mobile"
import { useMedicalChat } from "@/hooks/use-medical-chat"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ClinicalWorkspace() {
    const { interactionMode, activeCitation, closePDF } = useAppStore()
    const isMobile = useIsMobile()
    const { messages, isLoading, sendMessage } = useMedicalChat()

    const showChat = interactionMode === 'chat'
    const showPDF = !!activeCitation

    return (
        <Layout>
            <div className="relative h-full w-full flex overflow-hidden">
                {/* Main Chat Column */}
                <div className={`flex-1 flex flex-col relative h-full transition-all duration-300
          ${showPDF && !isMobile ? 'pr-0' : ''}`}
                >
                    {/* Chat Messages */}
                    {showChat && (
                        <ChatArea
                            messages={messages}
                            isLoading={isLoading}
                        />
                    )}

                    {/* Hero Search (Landing or Bottom Bar) */}
                    <HeroSearch onSendMessage={sendMessage} />
                </div>

                {/* PDF Side Panel - Desktop */}
                <AnimatePresence>
                    {showPDF && !isMobile && (
                        <motion.div
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: "40%", opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            className="h-full border-l border-white/10 relative z-20 shrink-0"
                        >
                            <PDFViewer
                                url={activeCitation?.url}
                                page={activeCitation?.page}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Mobile PDF Overlay */}
                <AnimatePresence>
                    {showPDF && isMobile && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
                        >
                            <motion.div
                                initial={{ y: "100%" }}
                                animate={{ y: 0 }}
                                exit={{ y: "100%" }}
                                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                className="absolute inset-x-2 bottom-2 top-16 glass-panel rounded-2xl overflow-hidden"
                            >
                                <PDFViewer
                                    url={activeCitation?.url}
                                    page={activeCitation?.page}
                                />
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </Layout>
    )
}
