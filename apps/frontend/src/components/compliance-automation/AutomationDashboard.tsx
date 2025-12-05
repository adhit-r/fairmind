'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { IconRobot, IconCalendar, IconAlertTriangle, IconFileText } from '@tabler/icons-react';

import ScheduleManager from './ScheduleManager';
import ViolationAlerts from './ViolationAlerts';
import ReportHistory from './ReportHistory';

export default function AutomationDashboard() {
    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-blue-100 rounded-lg text-blue-700">
                    <IconRobot size={32} />
                </div>
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Compliance Automation</h2>
                    <p className="text-muted-foreground">
                        Automate regulatory reporting, schedule audits, and track compliance violations.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Schedules & Reports */}
                <div className="lg:col-span-2 space-y-6">
                    <Tabs defaultValue="schedules" className="space-y-4">
                        <TabsList className="border-2 border-black p-0 h-auto bg-transparent gap-2">
                            <TabsTrigger
                                value="schedules"
                                className="data-[state=active]:bg-black data-[state=active]:text-white border-2 border-transparent data-[state=active]:border-black rounded-none px-4 py-2"
                            >
                                <IconCalendar size={18} className="mr-2" />
                                Schedules
                            </TabsTrigger>
                            <TabsTrigger
                                value="reports"
                                className="data-[state=active]:bg-black data-[state=active]:text-white border-2 border-transparent data-[state=active]:border-black rounded-none px-4 py-2"
                            >
                                <IconFileText size={18} className="mr-2" />
                                Report History
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="schedules">
                            <ScheduleManager />
                        </TabsContent>

                        <TabsContent value="reports">
                            <ReportHistory />
                        </TabsContent>
                    </Tabs>
                </div>

                {/* Right Column: Alerts */}
                <div className="lg:col-span-1">
                    <ViolationAlerts />
                </div>
            </div>
        </div>
    );
}
