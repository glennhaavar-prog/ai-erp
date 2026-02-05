'use client'

import { useState } from 'react'
import roadmapData from '../../kontali-roadmap-data.json'

type Status = 'done' | 'in-progress' | 'planned' | 'ideas'

const statusColors = {
  'done': 'bg-green-500/20 text-green-400 border-green-500/30',
  'in-progress': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'planned': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  'ideas': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
}

const statusLabels = {
  'done': 'Fullført',
  'in-progress': 'Pågår',
  'planned': 'Planlagt',
  'ideas': 'Ideer',
}

function ProgressRing({ progress, size = 120 }: { progress: number; size?: number }) {
  const radius = (size - 20) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (progress / 100) * circumference
  
  const color = progress >= 80 ? '#10b981' : progress >= 50 ? '#3b82f6' : progress >= 20 ? '#f59e0b' : '#ef4444'
  
  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="#334155"
        strokeWidth="8"
        fill="none"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke={color}
        strokeWidth="8"
        fill="none"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-500"
      />
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dy="0.3em"
        className="text-2xl font-bold fill-gray-100 transform rotate-90"
        style={{ transform: `rotate(90deg)`, transformOrigin: `${size/2}px ${size/2}px` }}
      >
        {progress}%
      </text>
    </svg>
  )
}

function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${statusColors[status]}`}>
      {statusLabels[status]}
    </span>
  )
}

function StatsCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className={`text-4xl font-bold ${color}`}>{value}</div>
    </div>
  )
}

export default function RoadmapPage() {
  const [selectedModule, setSelectedModule] = useState<any>(null)
  const [view, setView] = useState<'modules' | 'timeline'>('modules')
  
  const stats = roadmapData.stats
  
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-100 mb-2">
                Kontali ERP Roadmap
              </h1>
              <p className="text-gray-400">
                Komplett oversikt over systemet - Fullførte features, pågående arbeid og fremtidige planer
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setView('modules')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'modules'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                }`}
              >
                Moduler
              </button>
              <button
                onClick={() => setView('timeline')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  view === 'timeline'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                }`}
              >
                Timeline
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <StatsCard label="Total Progress" value={stats.overallProgress} color="text-blue-400" />
          <StatsCard label="Moduler Totalt" value={stats.totalModules} color="text-gray-100" />
          <StatsCard label="Fullført" value={stats.completedFeatures} color="text-green-400" />
          <StatsCard label="Pågår" value={stats.inProgressFeatures} color="text-blue-400" />
          <StatsCard label="Planlagt" value={stats.plannedFeatures} color="text-yellow-400" />
        </div>

        {view === 'modules' ? (
          <>
            {/* Module Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {roadmapData.modules.map((module) => (
                <div
                  key={module.id}
                  onClick={() => setSelectedModule(module)}
                  className="bg-slate-800 rounded-xl p-6 border-2 border-slate-700 hover:border-blue-500/50 cursor-pointer transition-all hover:shadow-xl hover:shadow-blue-500/10 group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-100 mb-2 group-hover:text-blue-400 transition-colors">
                        {module.name}
                      </h3>
                      <p className="text-sm text-gray-400 mb-3">
                        {module.description}
                      </p>
                      <StatusBadge status={module.status as Status} />
                    </div>
                    <div className="ml-4">
                      <ProgressRing progress={module.progress} size={80} />
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm text-gray-400 mt-4 pt-4 border-t border-slate-700">
                    <span>{module.features.length} features</span>
                    <span className="text-blue-400 font-medium group-hover:underline">
                      Se detaljer →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          /* Timeline View */
          <div className="bg-slate-800 rounded-xl p-8 border border-slate-700">
            <h2 className="text-2xl font-bold text-gray-100 mb-6">Roadmap Timeline</h2>
            <div className="space-y-6">
              {roadmapData.modules.map((module, idx) => (
                <div key={module.id} className="flex gap-6">
                  <div className="flex flex-col items-center">
                    <div className={`w-4 h-4 rounded-full ${
                      module.status === 'done' ? 'bg-green-500' :
                      module.status === 'in-progress' ? 'bg-blue-500' :
                      module.status === 'planned' ? 'bg-yellow-500' : 'bg-purple-500'
                    }`} />
                    {idx < roadmapData.modules.length - 1 && (
                      <div className="w-0.5 h-full bg-slate-700 mt-2" />
                    )}
                  </div>
                  <div className="flex-1 pb-8">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-bold text-gray-100">{module.name}</h3>
                      <StatusBadge status={module.status as Status} />
                      <span className="text-sm text-gray-400">{module.progress}%</span>
                    </div>
                    <p className="text-sm text-gray-400 mb-3">{module.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {module.features.map((feature) => (
                        <span
                          key={feature.id}
                          className="text-xs px-2 py-1 rounded bg-slate-700 text-gray-300"
                        >
                          {feature.name}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Module Detail Modal */}
      {selectedModule && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center p-6 z-50"
          onClick={() => setSelectedModule(null)}
        >
          <div
            className="bg-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto border-2 border-slate-700"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 p-6 flex items-start justify-between">
              <div>
                <h2 className="text-3xl font-bold text-gray-100 mb-2">
                  {selectedModule.name}
                </h2>
                <p className="text-gray-400">{selectedModule.description}</p>
              </div>
              <button
                onClick={() => setSelectedModule(null)}
                className="text-gray-400 hover:text-gray-100 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Status</div>
                  <StatusBadge status={selectedModule.status as Status} />
                </div>
                <div className="bg-slate-900 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Progress</div>
                  <div className="text-2xl font-bold text-blue-400">{selectedModule.progress}%</div>
                </div>
              </div>

              <h3 className="text-xl font-bold text-gray-100 mb-4">Features</h3>
              <div className="space-y-4">
                {selectedModule.features.map((feature: any) => (
                  <div key={feature.id} className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-lg font-semibold text-gray-100">{feature.name}</h4>
                      <StatusBadge status={feature.status as Status} />
                    </div>
                    <p className="text-sm text-gray-400 mb-3">{feature.description}</p>
                    
                    {feature.tasks && feature.tasks.length > 0 && (
                      <div className="mt-3">
                        <div className="text-xs font-semibold text-gray-400 mb-2">Tasks:</div>
                        <div className="space-y-1">
                          {feature.tasks.map((task: any, idx: number) => (
                            <div key={idx} className="flex items-center gap-2 text-sm">
                              <span className={`text-xs ${
                                task.status === 'done' ? 'text-green-400' :
                                task.status === 'in-progress' ? 'text-blue-400' :
                                'text-gray-500'
                              }`}>
                                {task.status === 'done' ? '✓' : task.status === 'in-progress' ? '◐' : '○'}
                              </span>
                              <span className={task.status === 'done' ? 'text-gray-400 line-through' : 'text-gray-300'}>
                                {task.name}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
