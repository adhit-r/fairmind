'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface EventsTimelineProps {
  data: Array<{ date: string; count: number }>;
  isLoading?: boolean;
}

export function EventsTimeline({ data, isLoading = false }: EventsTimelineProps) {
  return (
    <Card className="border-4 border-black shadow-brutal">
      <CardHeader className="border-b-4 border-black">
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
                  boxShadow: '6px 6px 0 rgba(0, 0, 0, 0.15)',
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
        )}
      </CardContent>
    </Card>
  );
}
