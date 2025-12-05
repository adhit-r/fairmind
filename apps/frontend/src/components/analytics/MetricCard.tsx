import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { IconArrowUp, IconArrowDown, IconMinus } from '@tabler/icons-react';

interface MetricCardProps {
    title: string;
    value: string | number;
    trend?: number; // Percentage change
    description?: string;
    icon?: React.ReactNode;
}

export default function MetricCard({ title, value, trend, description, icon }: MetricCardProps) {
    let trendColor = 'text-gray-500';
    let TrendIcon = IconMinus;

    if (trend !== undefined) {
        if (trend > 0) {
            trendColor = 'text-green-600';
            TrendIcon = IconArrowUp;
        } else if (trend < 0) {
            trendColor = 'text-red-600';
            TrendIcon = IconArrowDown;
        }
    }

    return (
        <Card className="border-2 border-black shadow-brutal">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                    {title}
                </CardTitle>
                {icon && <div className="text-muted-foreground">{icon}</div>}
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{value}</div>
                {(trend !== undefined || description) && (
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                        {trend !== undefined && (
                            <span className={`${trendColor} flex items-center font-medium`}>
                                <TrendIcon size={14} className="mr-1" />
                                {Math.abs(trend)}%
                            </span>
                        )}
                        {description && <span>{description}</span>}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
