'use client';

import { useEffect, useState } from 'react';
import { LayoutDashboard, MessageSquare } from 'lucide-react';
import TaskForm from '../components/TaskForm';
import TaskList from '../components/TaskList';
import ChatInterface from '../components/ChatInterface';
import { api } from '../lib/api';
import { Task } from '../types';

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'board' | 'chat'>('board');

  const fetchTasks = async () => {
    try {
      const response = await api.getTasks();
      setTasks(response.tasks);
    } catch (err: any) {
      console.error('Failed to fetch tasks:', err);
      if (err.message.includes('fetch')) {
        setError('Could not connect to backend. Is it running?');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleTaskCreated = (newTask: Task) => {
    setTasks((prev) => [newTask, ...prev]);
  };

  const handleTaskUpdated = (updatedTask: Task) => {
    setTasks((prev) => 
      prev.map((t) => (t.id === updatedTask.id ? updatedTask : t))
    );
  };

  const handleTaskDeleted = (deletedTaskId: number) => {
    setTasks((prev) => prev.filter((t) => t.id !== deletedTaskId));
  };

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            AI Task Manager
          </h1>
          <p className="text-gray-600">
            Organize your day with intelligent assistance
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white p-1 rounded-xl shadow-sm border border-gray-200 inline-flex">
            <button
              onClick={() => setActiveTab('board')}
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'board'
                  ? 'bg-blue-50 text-blue-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <LayoutDashboard className="w-4 h-4 mr-2" />
              Task Board
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'chat'
                  ? 'bg-blue-50 text-blue-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              AI Assistant
            </button>
          </div>
        </div>

        {activeTab === 'board' ? (
          <>
            <div className="mb-8">
              <TaskForm onTaskCreated={handleTaskCreated} />
            </div>

            {error && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-8 rounded-r-lg">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <span className="text-red-400">⚠️</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{error}</p>
                    <button 
                      onClick={() => { setError(null); setLoading(true); fetchTasks(); }}
                      className="mt-2 text-sm text-red-600 underline hover:text-red-500 font-medium"
                    >
                      Retry Connection
                    </button>
                  </div>
                </div>
              </div>
            )}

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600"></div>
                <p className="mt-4 text-gray-500 font-medium">Loading tasks...</p>
              </div>
            ) : (
              <TaskList 
                tasks={tasks} 
                onTaskUpdated={handleTaskUpdated} 
                onTaskDeleted={handleTaskDeleted}
                onRefresh={fetchTasks}
              />
            )}
          </>
        ) : (
          <div className="max-w-3xl mx-auto">
            <ChatInterface />
          </div>
        )}
      </div>
    </main>
  );
}