import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Activity, Clock, AlertCircle, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function PatientContextModal({ isOpen, onClose, onSubmit }) {
    const [formData, setFormData] = React.useState({
        symptoms: '',
        duration: '',
        severity: 'moderate',
        medicalHistory: '',
    })

    const handleSubmit = (e) => {
        e.preventDefault()
        onSubmit(formData)
        onClose()
    }

    const handleSkip = () => {
        onClose()
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={handleSkip}
                        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg"
                    >
                        <form onSubmit={handleSubmit} className="glass-panel rounded-2xl border border-white/20 shadow-2xl overflow-hidden">
                            {/* Header */}
                            <div className="flex items-center justify-between p-5 border-b border-white/10 bg-gradient-to-r from-primary/5 to-primary/10">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                                        <Activity className="w-5 h-5 text-primary" />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-semibold text-foreground">Tell us about your concern</h2>
                                        <p className="text-xs text-muted-foreground">This helps provide better guidance</p>
                                    </div>
                                </div>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={handleSkip}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>

                            {/* Content */}
                            <div className="p-5 space-y-4 max-h-[60vh] overflow-y-auto">
                                {/* Symptoms */}
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm font-medium text-foreground">
                                        <AlertCircle className="w-4 h-4 text-primary" />
                                        Symptoms
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.symptoms}
                                        onChange={(e) => setFormData({ ...formData, symptoms: e.target.value })}
                                        placeholder="e.g., headache, fatigue, nausea"
                                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        required
                                    />
                                </div>

                                {/* Duration */}
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm font-medium text-foreground">
                                        <Clock className="w-4 h-4 text-primary" />
                                        Duration
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.duration}
                                        onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                                        placeholder="e.g., 3 days, 2 weeks"
                                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        required
                                    />
                                </div>

                                {/* Severity */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-foreground">Severity</label>
                                    <div className="flex gap-2">
                                        {['mild', 'moderate', 'severe'].map((level) => (
                                            <button
                                                key={level}
                                                type="button"
                                                onClick={() => setFormData({ ...formData, severity: level })}
                                                className={cn(
                                                    "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                                                    formData.severity === level
                                                        ? "bg-primary text-primary-foreground"
                                                        : "bg-white/5 text-muted-foreground hover:bg-white/10"
                                                )}
                                            >
                                                {level.charAt(0).toUpperCase() + level.slice(1)}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Medical History */}
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm font-medium text-foreground">
                                        <FileText className="w-4 h-4 text-primary" />
                                        Medical History (Optional)
                                    </label>
                                    <textarea
                                        value={formData.medicalHistory}
                                        onChange={(e) => setFormData({ ...formData, medicalHistory: e.target.value })}
                                        placeholder="Allergies, medications, chronic conditions..."
                                        rows={3}
                                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground placeholder:text-muted-foreground/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                                    />
                                </div>

                                {/* Info Alert */}
                                <div className="flex gap-3 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                    <AlertCircle className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                                    <div className="text-xs text-blue-600 dark:text-blue-400">
                                        <p className="font-medium mb-1">Your privacy matters</p>
                                        <p>This information helps provide relevant guidance. It's stored securely and only used for this conversation.</p>
                                    </div>
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="flex gap-3 p-5 border-t border-white/10 bg-white/5">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={handleSkip}
                                    className="flex-1"
                                >
                                    Skip for now
                                </Button>
                                <Button
                                    type="submit"
                                    className="flex-1"
                                >
                                    Continue
                                </Button>
                            </div>
                        </form>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    )
}
