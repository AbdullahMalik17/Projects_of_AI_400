'use client';

import { useEffect, useState } from 'react';
import { LayoutDashboard, MessageSquare, Search, Filter, Calendar, AlertCircle, CheckCircle2 } from 'lucide-react';
import TaskForm from '../components/TaskForm';
import TaskList from '../components/TaskList';
import ChatInterface from '../components/ChatInterface';
import ProductivityDashboard from '../components/ProductivityDashboard';
import { api } from '../lib/api';
import { Task } from '../types';

type FilterType = 'all' | 'overdue' | 'upcoming' | 'high';

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'board' | 'chat'>('board');
  
  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');

  const fetchTasks = async () => {
    setLoading(true);
    try {
      let result;
      
      if (searchQuery.trim().length >= 2) {
        // Search takes precedence
        result = await api.searchTasks(searchQuery);
        setTasks(result); // Search returns Task[] directly
      } else {
        // Apply filters
        switch (activeFilter) {
          case 'overdue':
            result = await api.getOverdueTasks();
            setTasks(result);
            break;
          case 'upcoming':
            result = await api.getUpcomingTasks(7);
            setTasks(result);
            break;
          case 'high':
            const highPriResponse = await api.getTasks({ priority: 'high' });
            setTasks(highPriResponse.tasks);
            break;
          case 'all':
          default:
            const response = await api.getTasks();
            setTasks(response.tasks);
            break;
        }
      }
    } catch (err: any) {
      console.error('Failed to fetch tasks:', err);
      if (err.message?.includes('fetch')) {
        setError('Could not connect to backend. Is it running?');
      } else {
        setError(err.message || 'Failed to load tasks');
      }
    } finally {
      setLoading(false);
    }
  };

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTasks();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, activeFilter]);

  const handleTaskCreated = (newTask: Task) => {
    // If we're on 'all' or the new task matches current filter, add it.
    // Simplest approach: just refresh or add to top if 'all'.
    if (activeFilter === 'all' && !searchQuery) {
      setTasks((prev) => [newTask, ...prev]);
    } else {
      fetchTasks(); // Refresh to respect filters
    }
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

        {/* Main Navigation Tabs */}
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
            <ProductivityDashboard />

            <div className="mb-8">
              <TaskForm onTaskCreated={handleTaskCreated} />
            </div>

            {/* Search and Filters */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 flex flex-col md:flex-row gap-4 justify-between items-center">
              
              {/* Search Bar */}
              <div className="relative w-full md:w-64">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search tasks..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Filter Tabs */}
              <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
                <button
                  onClick={() => setActiveFilter('all')}
                  className={`flex items-center px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors border ${
                    activeFilter === 'all'
                      ? 'bg-gray-800 text-white border-gray-800'
                      : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  All Tasks
                </button>
                <button
                  onClick={() => setActiveFilter('upcoming')}
                  className={`flex items-center px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors border ${
                    activeFilter === 'upcoming'
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:bg-blue-50'
                  }`}
                >
                  <Calendar className="w-3 h-3 mr-1" />
                  Upcoming
                </button>
                <button
                  onClick={() => setActiveFilter('overdue')}
                  className={`flex items-center px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors border ${
                    activeFilter === 'overdue'
                      ? 'bg-red-600 text-white border-red-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:bg-red-50'
                  }`}
                >
                  <AlertCircle className="w-3 h-3 mr-1" />
                  Overdue
                </button>
                <button
                  onClick={() => setActiveFilter('high')}
                  className={`flex items-center px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors border ${
                    activeFilter === 'high'
                      ? 'bg-yellow-500 text-white border-yellow-500'
                      : 'bg-white text-gray-600 border-gray-300 hover:bg-yellow-50'
                  }`}
                >
                  High Priority
                </button>
              </div>
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
