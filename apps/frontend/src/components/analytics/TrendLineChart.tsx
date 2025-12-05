'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/card';

interface TrendLineChartProps {
    data: any[];
}

export function TrendLineChart({ data }: TrendLineChartProps) {
    return (
        <Card className="p-6 h-[400px] border-2 border-black shadow-brutal">
            <h3 className="text-lg font-bold mb-4">Bias Score Trend (30 Days)</h3>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip
                        contentStyle={{ border: '2px solid black', borderRadius: '0px' }}
                    />
                    <Legend />
                    <Line
                        type="monotone"
                        dataKey="bias_score"
                        stroke="#000000"
                        strokeWidth={3}
                        activeDot={{ r: 8 }}
                        name="Bias Score"
                    />
                    <Line
                        type="monotone"
                        dataKey="fairness_threshold"
                        stroke="#ff0000"
                        strokeDasharray="5 5"
                        name="Threshold"
                    />
                </LineChart>
            </ResponsiveContainer>
        </Card>
    );
}
