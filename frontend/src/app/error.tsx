'use client'

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  console.error(error)

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-900/50 border border-red-700 flex items-center justify-center">
          <span className="text-red-400 text-xl font-bold">!</span>
        </div>
        <h2 className="text-xl font-semibold text-gray-200 mb-2">Something went wrong</h2>
        <p className="text-gray-400 text-sm mb-6">{error.message || 'An unexpected error occurred.'}</p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => unstable_retry()}
            className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
          <a
            href="/dashboard/overview"
            className="px-4 py-2 text-sm font-medium bg-gray-800 text-gray-300 rounded hover:bg-gray-700 transition-colors"
          >
            Return to Dashboard
          </a>
        </div>
      </div>
    </div>
  )
}
