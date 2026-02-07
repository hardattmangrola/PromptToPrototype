import { useAppStore } from "@/store/useAppStore"
import { cn } from "@/lib/utils"
import { Stethoscope, User } from "lucide-react"

export function ModeToggle() {
    const { userMode, setUserMode } = useAppStore()

    return (
        (<div className="flex items-center bg-slate-100/50 dark:bg-slate-800/50 p-1 rounded-full border border-white/20 backdrop-blur-sm relative">
            <div
                className={cn(
                    "absolute top-1 bottom-1 w-[calc(50%-4px)] rounded-full bg-white dark:bg-slate-700 shadow-sm transition-all duration-300 ease-out",
                    userMode === 'doctor' ? "left-1" : "left-[calc(50%)]"
                )}
            />
            <button
                onClick={() => setUserMode('doctor')}
                className={cn(
                    "relative z-10 flex items-center justify-center gap-2 px-4 py-1.5 text-sm font-medium transition-colors duration-200 rounded-full w-32",
                    userMode === 'doctor' ? "text-primary dark:text-sky-400" : "text-muted-foreground hover:text-foreground"
                )}>
                <Stethoscope className="w-4 h-4" />
                Doctor
            </button>
            <button
                onClick={() => setUserMode('patient')}
                className={cn(
                    "relative z-10 flex items-center justify-center gap-2 px-4 py-1.5 text-sm font-medium transition-colors duration-200 rounded-full w-32",
                    userMode === 'patient' ? "text-secondary dark:text-emerald-400" : "text-muted-foreground hover:text-foreground"
                )}>
                <User className="w-4 h-4" />
                Patient
            </button>
        </div>)
    );
}
