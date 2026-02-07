import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, User, Bot, Loader2, FileText, AlertTriangle, Info } from "lucide-react"
import { cn } from "@/lib/utils"
import { MarkdownRenderer } from "./MarkdownRenderer"

/**
 * MessageBubble Component
 * Renders user or AI messages with optional reasoning accordion.
 * Shows special styling for refusals and limitations.
 */
export function MessageBubble({ message }) {
    const [showReasoning, setShowReasoning] = React.useState(false)
    const isUser = message.role === 'user'
    const isAI = message.role === 'ai'
    const isRefused = message.refused

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "flex gap-3 max-w-4xl",
                isUser ? "ml-auto flex-row-reverse" : ""
            )}
        >
            {/* Avatar */}
            <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                isUser
                    ? "bg-gradient-to-br from-primary to-secondary text-white"
                    : isRefused
                        ? "bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400"
                        : "glass-panel text-primary"
            )}>
                {isUser ? <User className="w-4 h-4" /> :
                    isRefused ? <AlertTriangle className="w-4 h-4" /> :
                        <Bot className="w-4 h-4" />}
            </div>

            {/* Message Content */}
            <div className={cn(
                "flex-1 max-w-[85%]",
                isUser && "text-right"
            )}>
                {/* User Message */}
                {isUser && (
                    <div className="inline-block glass-panel rounded-2xl rounded-tr-md px-4 py-3">
                        <p className="text-foreground">{message.content}</p>
                        {message.file && (
                            <div className="mt-2 flex items-center gap-2 text-xs text-primary bg-primary/10 w-fit px-2 py-1 rounded-md">
                                <FileText className="w-3 h-3" />
                                <span>{message.file.name}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* AI Message */}
                {isAI && (
                    <div className={cn(
                        "rounded-2xl rounded-tl-md overflow-hidden",
                        isRefused
                            ? "bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50"
                            : "glass-panel"
                    )}>
                        {/* Reasoning Accordion */}
                        {message.reasoning && (
                            <button
                                onClick={() => setShowReasoning(!showReasoning)}
                                className={cn(
                                    "w-full flex items-center justify-between px-4 py-2 text-xs transition-colors border-b",
                                    isRefused
                                        ? "text-amber-700 dark:text-amber-300 hover:bg-amber-100/50 dark:hover:bg-amber-900/30 border-amber-200 dark:border-amber-800/50"
                                        : "text-muted-foreground hover:bg-white/10 dark:hover:bg-slate-700/30 border-white/10"
                                )}
                            >
                                <span className="flex items-center gap-2">
                                    <Loader2 className={cn(
                                        "w-3 h-3",
                                        message.isLoading && !message.content && "animate-spin"
                                    )} />
                                    {isRefused ? "Refusal Reason" : "Thinking Process..."}
                                </span>
                                <ChevronDown className={cn(
                                    "w-4 h-4 transition-transform",
                                    showReasoning && "rotate-180"
                                )} />
                            </button>
                        )}

                        <AnimatePresence>
                            {showReasoning && message.reasoning && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                >
                                    <pre className={cn(
                                        "px-4 py-3 text-xs font-mono whitespace-pre-wrap",
                                        isRefused
                                            ? "bg-amber-100/50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300"
                                            : "bg-muted/30 text-muted-foreground"
                                    )}>
                                        {message.reasoning}
                                    </pre>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Main Content */}
                        <div className="px-4 py-3">
                            {message.isLoading && !message.content ? (
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span className="text-sm">Analyzing...</span>
                                </div>
                            ) : (
                                <>
                                    <MarkdownRenderer
                                        content={message.content}
                                        citations={message.citations || []}
                                    />

                                    {/* Limitations Disclaimer */}
                                    {message.limitations && !isRefused && (
                                        <div className="mt-4 pt-3 border-t border-border/50 flex items-start gap-2 text-xs text-muted-foreground">
                                            <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                                            <p>{message.limitations}</p>
                                        </div>
                                    )}

                                    {/* Confidence Indicator */}
                                    {message.confidence > 0 && !isRefused && (
                                        <div className="mt-4 pt-3 border-t border-white/10 flex items-center gap-2">
                                            <span className="text-xs text-muted-foreground">Confidence:</span>
                                            <div className="flex-1 h-1.5 bg-muted/30 rounded-full overflow-hidden max-w-[120px]">
                                                <div
                                                    className={cn(
                                                        "h-full rounded-full transition-all duration-500",
                                                        message.confidence >= 80 ? "confidence-high" :
                                                            message.confidence >= 50 ? "confidence-medium" : "confidence-low"
                                                    )}
                                                    style={{ width: `${message.confidence}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-medium text-foreground">{message.confidence}%</span>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    )
}
