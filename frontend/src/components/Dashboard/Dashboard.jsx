import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Calendar, Activity, BarChart2 } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Dashboard({ trends, sessions }) {
  const chartData = {
    labels: trends?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Stress Level',
        data: trends?.stressData || [3, 2, 5, 4, 2, 1, 3],
        borderColor: 'rgb(99, 102, 241)',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Positivity',
        data: trends?.positivityData || [5, 6, 4, 5, 7, 8, 6],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4,
      }
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 10,
      },
    },
  };

  return (
    <div className="w-full space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 flex items-center gap-4">
          <div className="p-3 bg-[rgba(108,99,255,0.2)] text-[#6C63FF] rounded-lg">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-sm text-[#8888AA] font-medium">Total Sessions</p>
            <p className="text-2xl font-bold text-white">{sessions?.length || 0}</p>
          </div>
        </div>
        
        <div className="glass-card p-6 flex items-center gap-4">
          <div className="p-3 bg-[rgba(67,233,123,0.2)] text-[#43E97B] rounded-lg">
            <BarChart2 size={24} />
          </div>
          <div>
            <p className="text-sm text-[#8888AA] font-medium">Avg Positivity</p>
            <p className="text-2xl font-bold text-white">7.2/10</p>
          </div>
        </div>
        
        <div className="glass-card p-6 flex items-center gap-4">
          <div className="p-3 bg-[rgba(255,179,71,0.2)] text-[#FFB347] rounded-lg">
            <Calendar size={24} />
          </div>
          <div>
            <p className="text-sm text-[#8888AA] font-medium">This Week</p>
            <p className="text-2xl font-bold text-white">4 Check-ins</p>
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-white mb-6">Emotion Trends</h3>
        <div className="w-full h-80">
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
}
