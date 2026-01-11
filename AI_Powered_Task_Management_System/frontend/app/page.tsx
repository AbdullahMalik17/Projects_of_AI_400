export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">
          AI-Powered Task Manager
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Intelligent task management with AI assistance
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-6 border border-gray-200 rounded-lg">
            <h2 className="text-xl font-semibold mb-2">Natural Language</h2>
            <p className="text-gray-600">
              Create tasks using natural conversation with AI
            </p>
          </div>
          <div className="p-6 border border-gray-200 rounded-lg">
            <h2 className="text-xl font-semibold mb-2">Smart Scheduling</h2>
            <p className="text-gray-600">
              AI-powered task prioritization and scheduling
            </p>
          </div>
          <div className="p-6 border border-gray-200 rounded-lg">
            <h2 className="text-xl font-semibold mb-2">Productivity Insights</h2>
            <p className="text-gray-600">
              Get intelligent insights about your work patterns
            </p>
          </div>
        </div>
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Frontend: Next.js | Backend: FastAPI | AI: Gemini
          </p>
        </div>
      </div>
    </main>
  );
}
