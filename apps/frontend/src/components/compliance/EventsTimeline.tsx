'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { describeChart } from '@/components/charts/describe'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface EventsTimelineProps {
  data: Array<{ date: string; count: number }>;
  isLoading?: boolean;
}

export function EventsTimeline({ data, isLoading = false }: EventsTimelineProps) {
  return (
    <Card className="fm-card">
      <CardHeader className="border-b border-[var(--fm-line)]">
        <CardTitle className="text-lg font-bold tracking-tight">EVENTS TIMELINE</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        {isLoading ? (
          <div className="h-80 flex items-center justify-center text-gray-500">
            Loading chart...
          </div>
        ) : data.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-gray-500">
            No data available
          </div>
        ) : (
          <div role="img" aria-label={describeChart('Events per day', data.map((d) => [d.date, d.count]))}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#000" />
                <XAxis
                  dataKey="date"
                  stroke="#000"
                  style={{ fontSize: '12px', fontWeight: 'bold' }}
                />
                <YAxis
                  stroke="#000"
                  style={{ fontSize: '12px', fontWeight: 'bold' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '2px solid #000',
                    boxShadow: 'var(--fm-shadow)',
                  }}
                  labelStyle={{ color: '#000', fontWeight: 'bold' }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#FF6B35"
                  strokeWidth={3}
                  dot={{ fill: '#FF6B35', r: 5, strokeWidth: 2 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
