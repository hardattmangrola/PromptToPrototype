import * as React from "react"
import { useAuth } from "@/auth/AuthProvider"
import { Button } from "@/components/ui/button"
import { AuthLayout, AuthHeader, FormField, LoadingButton, Divider } from "@/components/auth/AuthComponents"
import { AnimatePresence, motion } from "framer-motion"
import { Heart, Stethoscope, ArrowRight } from "lucide-react"

export function LoginPage({ onNavigate, onLoginSuccess }) {
    const { login, enterDemoMode } = useAuth()
    const [form, setForm] = React.useState({ email: "", password: "" })
    const [error, setError] = React.useState("")
    const [loading, setLoading] = React.useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError("")
        try {
            await login(form.email, form.password)
            onLoginSuccess?.()
        } catch (err) {
            setError(err.message || "Failed to login")
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout>
            <AuthHeader icon={Heart} title="Welcome back" subtitle="Sign in to continue" />

            <div className="glass-panel rounded-2xl p-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                    <FormField label="Email" type="email" placeholder="you@example.com" value={form.email} onChange={(v) => setForm(f => ({ ...f, email: v }))} required />
                    <FormField label="Password" type="password" placeholder="••••••••" value={form.password} onChange={(v) => setForm(f => ({ ...f, password: v }))} required />

                    <AnimatePresence>
                        {error && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-sm text-destructive text-center">{error}</motion.p>}
                    </AnimatePresence>

                    <LoadingButton loading={loading} type="submit" className="w-full h-10">Sign In</LoadingButton>
                </form>

                <Divider />
                <Button variant="outline" className="w-full h-10" onClick={() => { enterDemoMode?.('patient'); onLoginSuccess?.() }}>Try Demo</Button>
            </div>

            {/* Doctor Login */}
            <button onClick={() => onNavigate?.('doctor-login')} className="w-full mt-4 p-3 rounded-xl border border-border/50 bg-background/50 flex items-center gap-3 hover:bg-muted/50 transition-colors">
                <div className="w-9 h-9 rounded-lg bg-primary/5 flex items-center justify-center">
                    <Stethoscope className="w-4 h-4 text-primary" />
                </div>
                <div className="text-left flex-1">
                    <p className="text-sm font-medium">Healthcare Professional?</p>
                    <p className="text-xs text-muted-foreground">Login with NMC verification</p>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
            </button>

            <p className="mt-5 text-center text-sm text-muted-foreground">
                New here? <button onClick={() => onNavigate?.('register')} className="text-primary hover:underline">Create account</button>
            </p>
        </AuthLayout>
    )
}
