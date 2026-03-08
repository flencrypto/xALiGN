import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <SignUp 
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "shadow-xl border border-slate-200 dark:border-slate-700",
            headerTitle: "text-2xl font-bold",
            headerSubtitle: "text-slate-600 dark:text-slate-400",
          }
        }}
        fallbackRedirectUrl="/dashboard"
      />
    </div>
  )
}
