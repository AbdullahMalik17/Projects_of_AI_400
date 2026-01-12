'use client';

import { useState } from 'react';
import { api } from '../lib/api';
import { Task } from '../types';

interface TaskFormProps {
  onTaskCreated: (task: Task) => void;
}

export default function TaskForm({ onTaskCreated }: TaskFormProps) {
  const [mode, setMode] = useState<'structured' | 'natural'>('natural');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Natural Language State
  const [nlInput, setNlInput] = useState('');

  // Structured Input State
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [dueDate, setDueDate] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let task: Task;
      if (mode === 'natural') {
        if (!nlInput.trim()) return;
        task = await api.createTaskNaturalLanguage({ message: nlInput });
        setNlInput('');
      } else {
        if (!title.trim()) return;
        task = await api.createTask({
          title,
          priority,
          due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
        });
        setTitle('');
        setDueDate('');
        setPriority('medium');
      }
      onTaskCreated(task);
    } catch (err: any) {
      setError(err.message || 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
      <div className="flex gap-4 mb-4 border-b border-gray-100 pb-2">
        <button
          onClick={() => setMode('natural')}
          className={`pb-2 px-1 text-sm font-medium ${
            mode === 'natural'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Natural Language
        </button>
        <button
          onClick={() => setMode('structured')}
          className={`pb-2 px-1 text-sm font-medium ${
            mode === 'structured'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Structured Input
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'natural' ? (
          <div>
            <textarea
              value={nlInput}
              onChange={(e) => setNlInput(e.target.value)}
              placeholder="e.g., 'Remind me to call John tomorrow at 2pm about the project'"
              className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px] text-gray-900"
              disabled={loading}
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                placeholder="Task title"
                required
                disabled={loading}
              />
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as any)}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  disabled={loading}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  disabled={loading}
                />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
            {error}
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {loading ? 'Creating...' : mode === 'natural' ? 'Process with AI' : 'Create Task'}
          </button>
        </div>
      </form>
    </div>
  );
}
