'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/card';
import { CHART_TONES, chartTheme, seriesColor } from '@/lib/chart-theme';

interface TrendLineChartProps {
    data: any[];
}

export function TrendLineChart({ data }: TrendLineChartProps) {
    return (
        <Card className="h-[400px] p-4 sm:p-5">
            <h3 className="mb-4 text-base font-semibold">Bias Score Trend (30 Days)</h3>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid {...chartTheme.gridProps} />
                    <XAxis dataKey="date" {...chartTheme.axisProps} />
                    <YAxis domain={[0, 1]} {...chartTheme.axisProps} />
                    <Tooltip {...chartTheme.tooltipProps} />
                    <Legend {...chartTheme.legendProps} />
                    <Line
                        type="monotone"
                        dataKey="bias_score"
                        stroke={seriesColor(0)}
                        strokeWidth={2}
                        activeDot={{ r: 5 }}
                        name="Bias Score"
                    />
                    <Line
                        type="monotone"
                        dataKey="fairness_threshold"
                        stroke={CHART_TONES.critical}
                        strokeDasharray="5 5"
                        dot={false}
                        name="Threshold"
                    />
                </LineChart>
            </ResponsiveContainer>
        </Card>
    );
}
