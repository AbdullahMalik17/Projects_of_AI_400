'use client';

import { useEffect, useState } from 'react';
import { api } from '../lib/api';

interface ProductivityData {
  productivity_score: number;
  insights: string[];
  recommendations: string[];
  trend: 'improving' | 'stable' | 'declining';
}

export default function ProductivityDashboard() {
  const [data, setData] = useState<ProductivityData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getProductivityInsights();
        setData(result as ProductivityData);
      } catch (error) {
        console.error('Failed to fetch productivity insights:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="animate-pulse bg-gray-100 h-48 rounded-lg mb-8"></div>;
  if (!data) return null;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
      <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <span>📊</span> AI Productivity Insights
      </h2>
      
      <div className="grid md:grid-cols-3 gap-6">
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-500 mb-1">Productivity Score</div>
          <div className={`text-4xl font-bold ${getScoreColor(data.productivity_score)}`}>
            {data.productivity_score}
          </div>
          <div className="text-xs text-gray-400 mt-1 capitalize">{data.trend} Trend</div>
        </div>

        <div className="col-span-2 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Key Insights</h3>
            <ul className="space-y-1">
              {data.insights.map((insight, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-blue-500 mt-1">•</span>
                  {insight}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Recommendations</h3>
            <ul className="space-y-1">
              {data.recommendations.map((rec, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-purple-500 mt-1">✨</span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
