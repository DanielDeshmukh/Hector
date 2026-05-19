import { AlertCircle, X } from 'lucide-react'
import useAppStore from '../lib/store'

function ErrorMessage() {
  const { error, setError } = useAppStore()

  if (!error) return null

  return (
    <div className="pointer-events-none fixed inset-x-0 top-5 z-[70] flex justify-center px-5">
      <div className="pointer-events-auto flex w-full max-w-3xl items-start gap-4 rounded-2xl border border-error/40 bg-error/10 px-5 py-4 shadow-[0_12px_36px_rgba(239,68,68,0.12)] backdrop-blur-sm">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-error/25">
          <AlertCircle className="h-5 w-5 text-error" />
        </div>
        <span className="flex-1 pt-1 text-sm font-medium text-error/90">{error}</span>
        <button
          className="rounded-lg border border-transparent p-2 text-error/70 transition-all hover:border-error/30 hover:bg-error/15"
          onClick={() => setError(null)}
        >
          <X size={18} />
        </button>
      </div>
    </div>
  )
}

export default ErrorMessage