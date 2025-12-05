'use client'

import React from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Bar,
} from 'recharts'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface TrendDataPoint {
  timestamp: string
  score: number
  status: 'compliant' | 'non_compliant' | 'partial' | 'pending'
  requirements_met: number
  total_requirements: number
}

interface ComplianceTrendChartProps {
  framework: string
  trendData: TrendDataPoint[]
  timeframe: string
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'compliant':
      return '#10b981'
    case 'non_compliant':
      return '#ef4444'
    case 'partial':
      return '#f59e0b'
    case 'pending':
      return '#3b82f6'
    default:
      return '#6b7280'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white p-3 rounded-lg border border-gray-300 shadow-lg">
        <p className="text-sm font-semibold">{formatDate(data.timestamp)}</p>
        <p className="text-sm text-blue-600">Score: {data.score}%</p>
        <p className="text-sm text-gray-600">
          Requirements: {data.requirements_met}/{data.total_requirements}
        </p>
        <p className="text-xs text-gray-500 mt-1 capitalize">{data.status.replace('_', ' ')}</p>
      </div>
    )
  }
  return null
}

export const ComplianceTrendChart: React.FC<ComplianceTrendChartProps> = ({
  framework,
  trendData,
  timeframe,
}) => {
  if (!trendData || trendData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Compliance Trends</CardTitle>
          <CardDescription>No trend data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Insufficient data to display trends</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const sortedData = [...trendData].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  const firstScore = sortedData[0].score
  const lastScore = sortedData[sortedData.length - 1].score
  const improvement = lastScore - firstScore
  const isImproving = improvement >= 0

  const avgScore = Math.round(
    sortedData.reduce((sum, d) => sum + d.score, 0) / sortedData.length
  )

  const maxScore = Math.max(...sortedData.map(d => d.score))
  const minScore = Math.min(...sortedData.map(d => d.score))

  const chartData = sortedData.map(d => ({
    ...d,
    date: formatDate(d.timestamp),
  }))

  return (
    <div className="space-y-6">
      {/* Trend Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance Trends</CardTitle>
          <CardDescription>
            Historical compliance scores for {framework} over {timeframe}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-gray-600">Current Score</p>
              <p className="text-2xl font-bold text-blue-600">{lastScore}%</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
              <p className="text-sm text-gray-600">Average Score</p>
              <p className="text-2xl font-bold text-purple-600">{avgScore}%</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <p className="text-sm text-gray-600">Highest Score</p>
              <p className="text-2xl font-bold text-green-600">{maxScore}%</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <p className="text-sm text-gray-600">Lowest Score</p>
              <p className="text-2xl font-bold text-red-600">{minScore}%</p>
            </div>
          </div>

          {/* Trend Indicator */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Overall Trend</p>
              <p className="text-lg font-semibold text-gray-800">
                {isImproving ? 'Improving' : 'Declining'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {isImproving ? '+' : ''}{improvement.toFixed(1)}% change from start
              </p>
            </div>
            {isImproving ? (
              <TrendingUp className="h-8 w-8 text-green-600" />
            ) : (
              <TrendingDown className="h-8 w-8 text-red-600" />
            )}
          </div>
        </CardContent>
      </Card>

      {/* Score Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance Score Over Time</CardTitle>
          <CardDescription>Line chart showing compliance score progression</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorScore)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Requirements Met Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Requirements Met Over Time</CardTitle>
          <CardDescription>
            Tracking the number of requirements met vs total requirements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="requirements_met" fill="#10b981" name="Requirements Met" />
              <Bar dataKey="total_requirements" fill="#e5e7eb" name="Total Requirements" />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Status Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Status Distribution</CardTitle>
          <CardDescription>Breakdown of compliance statuses over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {sortedData.map((point, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{formatDate(point.timestamp)}</p>
                  <p className="text-xs text-gray-600">
                    {point.requirements_met}/{point.total_requirements} requirements met
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${point.score}%` }}
                    />
                  </div>
                  <Badge
                    className={`ml-2 ${
                      point.status === 'compliant'
                        ? 'bg-green-100 text-green-800'
                        : point.status === 'non_compliant'
                          ? 'bg-red-100 text-red-800'
                          : point.status === 'partial'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {point.score}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ComplianceTrendChart
