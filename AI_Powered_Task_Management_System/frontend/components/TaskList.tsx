'use client';

import { useState } from 'react';
import { api } from '../lib/api';
import { Task, TaskStatus } from '../types';

interface TaskListProps {
  tasks: Task[];
  onTaskUpdated: (task: Task) => void;
  onTaskDeleted: (taskId: number) => void;
  onRefresh: () => void;
}

export default function TaskList({ tasks, onTaskUpdated, onTaskDeleted, onRefresh }: TaskListProps) {
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [breakingDownId, setBreakingDownId] = useState<number | null>(null);

  const handleStatusChange = async (task: Task, newStatus: TaskStatus) => {
    setUpdatingId(task.id);
    try {
      let updatedTask;
      if (newStatus === 'completed') {
        updatedTask = await api.completeTask(task.id);
      } else {
        updatedTask = await api.updateTask(task.id, { status: newStatus });
      }
      onTaskUpdated(updatedTask);
    } catch (error) {
      console.error('Failed to update task:', error);
      alert('Failed to update task status');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDelete = async (taskId: number) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    setUpdatingId(taskId);
    try {
      await api.deleteTask(taskId);
      onTaskDeleted(taskId);
    } catch (error) {
      console.error('Failed to delete task:', error);
      alert('Failed to delete task');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleBreakdown = async (task: Task) => {
    setBreakingDownId(task.id);
    try {
      // 1. Get suggestions
      const suggestions = await api.suggestBreakdown(task.id);
      
      if (suggestions.length === 0) {
        alert('AI could not generate suggestions.');
        return;
      }

      // 2. Review (Simple Confirm for now)
      const message = `AI Suggested Subtasks:\n\n${suggestions.map(s => `• ${s}`).join('\n')}\n\nCreate these subtasks?`;
      if (!confirm(message)) return;

      // 3. Create
      await api.breakdownTask(task.id, suggestions);
      onRefresh(); 
    } catch (error) {
      console.error('Failed to break down task:', error);
      alert('Failed to break down task');
    } finally {
      setBreakingDownId(null);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Filter out subtasks from the main list (they will be rendered under their parents)
  // This assumes the API returns all tasks flat or we have a way to distinguish.
  // Actually, if the API returns a flat list including subtasks, we might see duplicates if we render them nested.
  // But typically a list endpoint returns root tasks if configured, or all tasks.
  // Let's assume for now we render provided 'tasks' as root items. 
  // If 'tasks' contains everything flat, we should filter.
  // Checking types: Task has parent_task_id.
  const rootTasks = tasks.filter(t => !t.parent_task_id);

  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">No tasks found. Create one to get started!</p>
      </div>
    );
  }

  const renderTask = (task: Task, isSubtask = false) => (
    <div 
      key={task.id} 
      className={`bg-white p-4 rounded-lg shadow-sm border border-gray-200 transition-opacity ${
        (updatingId === task.id || breakingDownId === task.id) ? 'opacity-50 pointer-events-none' : ''
      } ${isSubtask ? 'ml-8 mt-2 border-l-4 border-l-gray-300' : ''}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className={`font-semibold text-lg ${
              task.status === 'completed' ? 'line-through text-gray-400' : 'text-gray-900'
            }`}>
              {task.title}
            </h3>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
              {task.priority}
            </span>
          </div>
          
          {task.description && (
            <p className="text-gray-600 text-sm mb-2">{task.description}</p>
          )}

          <div className="flex flex-wrap gap-2 text-xs text-gray-500">
            {task.due_date && (
              <span className="flex items-center gap-1">
                📅 {new Date(task.due_date).toLocaleDateString()}
                {' '}
                {new Date(task.due_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
            {task.tags && task.tags.map((tag) => (
              <span key={tag.id} className="bg-gray-100 px-2 py-0.5 rounded">
                #{tag.name}
              </span>
            ))}
            {task.task_metadata?.reasoning && (
              <div className="w-full mt-2 p-2 bg-purple-50 text-purple-800 rounded border border-purple-100 italic">
                ✨ AI Insight: {task.task_metadata.reasoning}
              </div>
            )}
            {task.task_metadata?.estimation_accuracy && (
              <span className="text-green-600 font-medium">
                🎯 Accuracy: {task.task_metadata.estimation_accuracy}%
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2 items-end">
          <select
            value={task.status}
            onChange={(e) => handleStatusChange(task, e.target.value as TaskStatus)}
            className="text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 text-gray-900"
          >
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>

          {/* AI Actions */}
          {task.status !== 'completed' && (!task.subtasks || task.subtasks.length === 0) && !isSubtask && (
            <div className="flex gap-2">
              <button
                onClick={() => handleBreakdown(task)}
                className="text-purple-600 hover:text-purple-800 text-xs font-medium flex items-center gap-1"
                disabled={breakingDownId === task.id}
              >
                {breakingDownId === task.id ? 'Thinking...' : '✨ Breakdown'}
              </button>
              <button
                onClick={async () => {
                  try {
                    const schedule = await api.scheduleTask(task.id);
                    alert(`📅 AI Suggestion:\n\nTime: ${new Date(schedule.suggested_start_time).toLocaleString()}\nDuration: ${schedule.suggested_duration_minutes} mins\n\nReasoning: ${schedule.reasoning}`);
                  } catch (e) {
                    alert('Failed to get schedule suggestion');
                  }
                }}
                className="text-blue-600 hover:text-blue-800 text-xs font-medium flex items-center gap-1"
              >
                📅 Schedule
              </button>
            </div>
          )}
          
          <button
            onClick={() => handleDelete(task.id)}
            className="text-red-600 hover:text-red-800 text-xs font-medium"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Render Subtasks */}
      {task.subtasks && task.subtasks.length > 0 && (
        <div className="mt-2 space-y-2">
          {task.subtasks.map(subtask => renderTask(subtask, true))}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {rootTasks.map(task => renderTask(task))}
    </div>
  );
}