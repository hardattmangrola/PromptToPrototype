import { Layout } from "@/components/layout/Layout"
import { HeroSearch } from "@/components/landing/HeroSearch"
import { ChatArea } from "@/components/chat/ChatArea"
import { PDFViewer } from "@/components/reference/PDFViewer"
import { SettingsModal } from "@/components/layout/SettingsModal"
import { PatientContextModal } from "@/components/PatientContextModal"
import { useAppStore } from "@/store/useAppStore"
import { AnimatePresence, motion } from "framer-motion"
import { useIsMobile } from "@/hooks/use-mobile"
import { useMedicalChat } from "@/hooks/use-medical-chat"
import { EyeOff } from "lucide-react"
import { cn } from "@/lib/utils"
import * as React from "react"

export function ClinicalWorkspace() {
    const { interactionMode, activeCitation, closePDF, activeChatId, setPatientContext, getActiveChat } = useAppStore()
    const isMobile = useIsMobile()
    const [showContextModal, setShowContextModal] = React.useState(false)
    const { messages, isLoading, sendMessage, isIncognito, triggerContextModal } = useMedicalChat()

    const showChat = interactionMode === 'chat'
    const showPDF = !!activeCitation

    const handleContextSubmit = (context) => {
        if (activeChatId) {
            setPatientContext(activeChatId, context)
        }
        setShowContextModal(false)
    }

    // Listen for context modal trigger from chat hook
    React.useEffect(() => {
        if (triggerContextModal) {
            const activeChat = getActiveChat()
            if (!activeChat?.isIncognito && !activeChat?.patientContext) {
                setShowContextModal(true)
            }
        }
    }, [triggerContextModal, getActiveChat, activeChatId])

    return (
        <Layout>
            {/* Settings Modal */}
            <SettingsModal />

            {/* Patient Context Modal */}
            <PatientContextModal
                isOpen={showContextModal}
                onClose={() => setShowContextModal(false)}
                onSubmit={handleContextSubmit}
            />


            {/* Incognito Banner */}
            <AnimatePresence>
                {isIncognito && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="absolute top-14 left-0 right-0 z-30 flex justify-center pointer-events-none"
                    >
                        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-purple-500/20 to-violet-500/20 border border-purple-500/30 backdrop-blur-sm">
                            <EyeOff className="w-3.5 h-3.5 text-purple-400" />
                            <span className="text-xs text-purple-300 font-medium">Incognito Mode</span>
                            <span className="text-[10px] text-purple-400/70">• Chat not saved</span>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className={cn(
                "relative h-full w-full flex overflow-hidden transition-all duration-500",
                isIncognito && "incognito-mode"
            )}>
                {/* Main Chat Column */}
                <div className={cn(
                    "flex-1 flex flex-col relative h-full transition-all duration-300",
                    showPDF && !isMobile && "pr-0"
                )}>
                    {/* Chat Messages */}
                    {showChat && (
                        <ChatArea
                            messages={messages}
                            isLoading={isLoading}
                            isIncognito={isIncognito}
                        />
                    )}

                    {/* Hero Search (Landing or Bottom Bar) */}
                    <HeroSearch onSendMessage={sendMessage} isIncognito={isIncognito} />
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
