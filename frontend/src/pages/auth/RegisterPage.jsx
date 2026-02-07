import * as React from "react"
import { useAuth } from "@/auth/AuthProvider"
import { Button } from "@/components/ui/button"
import { AuthLayout, AuthHeader, FormField, LoadingButton, Divider } from "@/components/auth/AuthComponents"
import { AnimatePresence, motion } from "framer-motion"
import { UserPlus } from "lucide-react"

export function RegisterPage({ onNavigate, onLoginSuccess }) {
    const { register, enterDemoMode } = useAuth()
    const [form, setForm] = React.useState({ name: "", email: "", password: "" })
    const [error, setError] = React.useState("")
    const [loading, setLoading] = React.useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError("")
        try {
            await register(form.email, form.password, form.name)
            onLoginSuccess?.()
        } catch (err) {
            setError(err.message || "Failed to register")
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout>
            <AuthHeader icon={UserPlus} title="Create account" subtitle="Get started for free" iconClass="bg-secondary/10 text-secondary" />

            <div className="glass-panel rounded-2xl p-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                    <FormField label="Full Name" placeholder="Your name" value={form.name} onChange={(v) => setForm(f => ({ ...f, name: v }))} required />
                    <FormField label="Email" type="email" placeholder="you@example.com" value={form.email} onChange={(v) => setForm(f => ({ ...f, email: v }))} required />
                    <FormField label="Password" type="password" placeholder="••••••••" value={form.password} onChange={(v) => setForm(f => ({ ...f, password: v }))} required />

                    <AnimatePresence>
                        {error && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-sm text-destructive text-center">{error}</motion.p>}
                    </AnimatePresence>

                    <LoadingButton loading={loading} type="submit" className="w-full h-10 bg-secondary hover:bg-secondary/90">Create Account</LoadingButton>
                </form>

                <Divider />
                <Button variant="outline" className="w-full h-10" onClick={() => { enterDemoMode?.('patient'); onLoginSuccess?.() }}>Try Demo</Button>
            </div>

            <p className="mt-5 text-center text-sm text-muted-foreground">
                Already have an account? <button onClick={() => onNavigate?.('login')} className="text-secondary hover:underline">Sign in</button>
            </p>
        </AuthLayout>
    )
}
