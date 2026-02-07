import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, BrainCircuit, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function ThinkingProcess({ steps = [], isThinking = false }) {
    const [isOpen, setIsOpen] = React.useState(true)

    if (!steps.length && !isThinking) return null

    return (
        (<div className="w-full max-w-3xl mx-auto mb-6">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 text-xs font-mono text-muted-foreground hover:text-primary transition-colors mb-2"
            >
                <BrainCircuit className={cn("h-3 w-3", isThinking && "animate-pulse text-sky-500")} />
                <span>Reasoning Trace</span>
                <ChevronDown className={cn("h-3 w-3 transition-transform", isOpen && "rotate-180")} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="glass-panel rounded-lg p-3 bg-white/30 dark:bg-slate-900/30 border-white/10 space-y-2">
                            {steps.map((step, index) => (
                                <div key={index} className="flex items-start gap-3 text-xs font-mono text-muted-foreground/80">
                                    <div className="min-w-[16px] pt-0.5 text-right opacity-50">{index + 1}.</div>
                                    <div className="break-words leading-relaxed">
                                        {step}
                                    </div>
                                </div>
                            ))}
                            {isThinking && (
                                <div className="flex items-center gap-3 text-xs font-mono text-sky-500/80 animate-pulse">
                                    <div className="min-w-[16px] flex justify-end">
                                        <Loader2 className="h-3 w-3 animate-spin" />
                                    </div>
                                    <div>Processing clinical data...</div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>)
    );
}
