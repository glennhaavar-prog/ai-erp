"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

// Enums matching backend
const TaskStatus = {
  NOT_STARTED: "not_started",
  IN_PROGRESS: "in_progress",
  COMPLETED: "completed",
  DEVIATION: "deviation",
} as const;

const TaskCategory = {
  AVSTEMMING: "avstemming",
  RAPPORTERING: "rapportering",
  BOKFORING: "bokføring",
  COMPLIANCE: "compliance",
} as const;

const TaskFrequency = {
  MONTHLY: "monthly",
  QUARTERLY: "quarterly",
  YEARLY: "yearly",
  AD_HOC: "ad_hoc",
} as const;

interface Task {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  frequency: string | null;
  period_year: number;
  period_month: number | null;
  due_date: string | null;
  status: string;
  completed_by: string | null;
  completed_at: string | null;
  documentation_url: string | null;
  ai_comment: string | null;
  subtasks?: Task[];
}

interface TaskStats {
  total: number;
  completed: number;
  in_progress: number;
  not_started: number;
  deviations: number;
}

export default function OppgaverPage() {
  const pathname = usePathname();
  const clientId = pathname?.split('/')[2] || "8f6d593d-cb4e-42eb-a51c-a7b1dab660dc";

  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<TaskStats>({
    total: 0,
    completed: 0,
    in_progress: 0,
    not_started: 0,
    deviations: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [periodYear] = useState<number>(2024);
  const [periodMonth] = useState<number | null>(null);
  
  // Selected task for detail view
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);
  const [showEditTaskForm, setShowEditTaskForm] = useState(false);

  // New/Edit task form data
  const [taskForm, setTaskForm] = useState({
    name: "",
    description: "",
    category: "",
    frequency: TaskFrequency.MONTHLY,
    due_date: "",
  });

  useEffect(() => {
    fetchTasks();
  }, [clientId, periodYear, periodMonth, statusFilter, categoryFilter]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        client_id: clientId,
        period_year: periodYear.toString(),
      });

      if (periodMonth) params.append("period_month", periodMonth.toString());
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (categoryFilter !== "all") params.append("category", categoryFilter);

      const response = await fetch(
        `http://localhost:8000/api/tasks?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTasks(data.tasks);
      setStats({
        total: data.total,
        completed: data.completed,
        in_progress: data.in_progress,
        not_started: data.not_started,
        deviations: data.deviations,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const fetchTaskDetails = async (taskId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/tasks/${taskId}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSelectedTask(data);
    } catch (err) {
      console.error("Error fetching task details:", err);
    }
  };

  const createTask = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/tasks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          client_id: clientId,
          name: taskForm.name,
          description: taskForm.description || null,
          category: taskForm.category || null,
          frequency: taskForm.frequency,
          period_year: periodYear,
          period_month: periodMonth,
          due_date: taskForm.due_date || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Reset form and refresh
      setTaskForm({
        name: "",
        description: "",
        category: "",
        frequency: TaskFrequency.MONTHLY,
        due_date: "",
      });
      setShowNewTaskForm(false);
      fetchTasks();
    } catch (err) {
      console.error("Error creating task:", err);
      alert("Feil ved opprettelse av oppgave");
    }
  };

  const updateTask = async () => {
    if (!selectedTask) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/tasks/${selectedTask.id}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: taskForm.name,
            description: taskForm.description || null,
            category: taskForm.category || null,
            frequency: taskForm.frequency,
            due_date: taskForm.due_date || null,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Reset form and refresh
      setShowEditTaskForm(false);
      fetchTasks();
      fetchTaskDetails(selectedTask.id);
    } catch (err) {
      console.error("Error updating task:", err);
      alert("Feil ved oppdatering av oppgave");
    }
  };

  const completeTask = async (taskId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/tasks/${taskId}/complete`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            completed_by: "Bruker",
            notes: "Manuelt merket som fullført",
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      fetchTasks();
      if (selectedTask?.id === taskId) {
        fetchTaskDetails(taskId);
      }
    } catch (err) {
      console.error("Error completing task:", err);
      alert("Feil ved fullføring av oppgave");
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      [TaskStatus.NOT_STARTED]: {
        label: "Ikke startet",
        className: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
      },
      [TaskStatus.IN_PROGRESS]: {
        label: "Pågående",
        className: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
      },
      [TaskStatus.COMPLETED]: {
        label: "Fullført",
        className: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
      },
      [TaskStatus.DEVIATION]: {
        label: "Avvik",
        className: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
      },
    };

    const badge = badges[status as keyof typeof badges] || badges[TaskStatus.NOT_STARTED];

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.className}`}>
        {badge.label}
      </span>
    );
  };

  const getCategoryLabel = (category: string | null) => {
    if (!category) return "Ingen kategori";
    const labels = {
      [TaskCategory.AVSTEMMING]: "Avstemming",
      [TaskCategory.RAPPORTERING]: "Rapportering",
      [TaskCategory.BOKFORING]: "Bokføring",
      [TaskCategory.COMPLIANCE]: "Compliance",
    };
    return labels[category as keyof typeof labels] || category;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Ingen frist";
    const date = new Date(dateString);
    return date.toLocaleDateString("nb-NO");
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">
            Feil ved henting av oppgaver: {error}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Oppgaver
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Oversikt over oppgaver for {periodYear}
            {periodMonth && ` - ${periodMonth.toString().padStart(2, "0")}`}
          </p>
        </div>
        <button
          onClick={() => {
            setTaskForm({
              name: "",
              description: "",
              category: "",
              frequency: TaskFrequency.MONTHLY,
              due_date: "",
            });
            setShowNewTaskForm(true);
            setSelectedTask(null);
          }}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
        >
          + Ny oppgave
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Totalt</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {stats.total}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Fullført</div>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
            {stats.completed}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Pågående</div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
            {stats.in_progress}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Ikke startet</div>
          <div className="text-2xl font-bold text-gray-600 dark:text-gray-400 mt-1">
            {stats.not_started}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Avvik</div>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
            {stats.deviations}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="all">Alle</option>
            <option value={TaskStatus.NOT_STARTED}>Ikke startet</option>
            <option value={TaskStatus.IN_PROGRESS}>Pågående</option>
            <option value={TaskStatus.COMPLETED}>Fullført</option>
            <option value={TaskStatus.DEVIATION}>Avvik</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Kategori
          </label>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="all">Alle</option>
            <option value={TaskCategory.AVSTEMMING}>Avstemming</option>
            <option value={TaskCategory.RAPPORTERING}>Rapportering</option>
            <option value={TaskCategory.BOKFORING}>Bokføring</option>
            <option value={TaskCategory.COMPLIANCE}>Compliance</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task List */}
        <div className="space-y-3">
          {tasks.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                Ingen oppgaver funnet
              </p>
            </div>
          ) : (
            tasks.map((task) => (
              <div
                key={task.id}
                onClick={() => {
                  fetchTaskDetails(task.id);
                  setShowNewTaskForm(false);
                  setShowEditTaskForm(false);
                }}
                className={`bg-white dark:bg-gray-800 border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                  selectedTask?.id === task.id
                    ? "border-blue-500 dark:border-blue-400"
                    : "border-gray-200 dark:border-gray-700"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {task.name}
                      </h3>
                      {getStatusBadge(task.status)}
                    </div>
                    {task.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {task.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                      {task.category && (
                        <span>📁 {getCategoryLabel(task.category)}</span>
                      )}
                      {task.due_date && (
                        <span>📅 {formatDate(task.due_date)}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detail Panel */}
        <div>
          {showNewTaskForm ? (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Ny oppgave
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tittel *
                  </label>
                  <input
                    type="text"
                    value={taskForm.name}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, name: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Beskrivelse
                  </label>
                  <textarea
                    value={taskForm.description}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, description: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Kategori
                  </label>
                  <select
                    value={taskForm.category}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, category: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Ingen kategori</option>
                    <option value={TaskCategory.AVSTEMMING}>Avstemming</option>
                    <option value={TaskCategory.RAPPORTERING}>Rapportering</option>
                    <option value={TaskCategory.BOKFORING}>Bokføring</option>
                    <option value={TaskCategory.COMPLIANCE}>Compliance</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Frekvens
                  </label>
                  <select
                    value={taskForm.frequency}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, frequency: e.target.value as any })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value={TaskFrequency.MONTHLY}>Månedlig</option>
                    <option value={TaskFrequency.QUARTERLY}>Kvartalsvis</option>
                    <option value={TaskFrequency.YEARLY}>Årlig</option>
                    <option value={TaskFrequency.AD_HOC}>Ad-hoc</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Forfallsdato
                  </label>
                  <input
                    type="date"
                    value={taskForm.due_date}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, due_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={createTask}
                    disabled={!taskForm.name}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium transition-colors"
                  >
                    Opprett
                  </button>
                  <button
                    onClick={() => setShowNewTaskForm(false)}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-md font-medium transition-colors"
                  >
                    Avbryt
                  </button>
                </div>
              </div>
            </div>
          ) : showEditTaskForm && selectedTask ? (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Rediger oppgave
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tittel *
                  </label>
                  <input
                    type="text"
                    value={taskForm.name}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, name: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Beskrivelse
                  </label>
                  <textarea
                    value={taskForm.description}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, description: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Kategori
                  </label>
                  <select
                    value={taskForm.category}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, category: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Ingen kategori</option>
                    <option value={TaskCategory.AVSTEMMING}>Avstemming</option>
                    <option value={TaskCategory.RAPPORTERING}>Rapportering</option>
                    <option value={TaskCategory.BOKFORING}>Bokføring</option>
                    <option value={TaskCategory.COMPLIANCE}>Compliance</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Frekvens
                  </label>
                  <select
                    value={taskForm.frequency}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, frequency: e.target.value as any })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value={TaskFrequency.MONTHLY}>Månedlig</option>
                    <option value={TaskFrequency.QUARTERLY}>Kvartalsvis</option>
                    <option value={TaskFrequency.YEARLY}>Årlig</option>
                    <option value={TaskFrequency.AD_HOC}>Ad-hoc</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Forfallsdato
                  </label>
                  <input
                    type="date"
                    value={taskForm.due_date}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, due_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={updateTask}
                    disabled={!taskForm.name}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium transition-colors"
                  >
                    Lagre
                  </button>
                  <button
                    onClick={() => setShowEditTaskForm(false)}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-md font-medium transition-colors"
                  >
                    Avbryt
                  </button>
                </div>
              </div>
            </div>
          ) : selectedTask ? (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {selectedTask.name}
                  </h2>
                  <div className="mt-2">{getStatusBadge(selectedTask.status)}</div>
                </div>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>

              {selectedTask.description && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Beskrivelse
                  </h3>
                  <p className="text-gray-900 dark:text-white">
                    {selectedTask.description}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                {selectedTask.category && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Kategori
                    </h3>
                    <p className="text-gray-900 dark:text-white">
                      {getCategoryLabel(selectedTask.category)}
                    </p>
                  </div>
                )}
                {selectedTask.due_date && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Forfallsdato
                    </h3>
                    <p className="text-gray-900 dark:text-white">
                      {formatDate(selectedTask.due_date)}
                    </p>
                  </div>
                )}
              </div>

              {selectedTask.completed_by && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Fullført av
                  </h3>
                  <p className="text-gray-900 dark:text-white">
                    {selectedTask.completed_by}
                    {selectedTask.completed_at && (
                      <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                        ({formatDate(selectedTask.completed_at)})
                      </span>
                    )}
                  </p>
                </div>
              )}

              {selectedTask.ai_comment && (
                <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
                  <h3 className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-1">
                    🤖 AI Kommentar
                  </h3>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {selectedTask.ai_comment}
                  </p>
                </div>
              )}

              {selectedTask.subtasks && selectedTask.subtasks.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Deloppgaver ({selectedTask.subtasks.length})
                  </h3>
                  <div className="space-y-2">
                    {selectedTask.subtasks.map((subtask) => (
                      <div
                        key={subtask.id}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-md"
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {subtask.name}
                          </p>
                          {subtask.description && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {subtask.description}
                            </p>
                          )}
                        </div>
                        {getStatusBadge(subtask.status)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                {selectedTask.status !== TaskStatus.COMPLETED && (
                  <button
                    onClick={() => completeTask(selectedTask.id)}
                    className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md font-medium transition-colors"
                  >
                    ✓ Merk som fullført
                  </button>
                )}
                <button
                  onClick={() => {
                    setTaskForm({
                      name: selectedTask.name,
                      description: selectedTask.description || "",
                      category: selectedTask.category || "",
                      frequency: (selectedTask.frequency || TaskFrequency.MONTHLY) as any,
                      due_date: selectedTask.due_date || "",
                    });
                    setShowEditTaskForm(true);
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
                >
                  ✏️ Rediger
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                Velg en oppgave for å se detaljer
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
