import { SelectionProvider } from '@/context/SelectionContext'
import { HeatmapView } from '@/components/heatmap/HeatmapView'

export function App() {
  return (
    <SelectionProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
        <header className="border-b border-white/10 bg-white/5 backdrop-blur-sm">
          <div className="mx-auto max-w-7xl px-6 py-4">
            <h1 className="text-xl font-bold tracking-tight">Job Evolution Tracker</h1>
            <p className="text-sm text-slate-400">
              AI automatability analysis across industries
            </p>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-6 py-8">
          <HeatmapView />
        </main>
      </div>
    </SelectionProvider>
  )
}
