'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { IconPlus, IconCalendar, IconTrash } from '@tabler/icons-react';
import { complianceAutomationService, ComplianceSchedule } from '@/lib/api/compliance-automation-service';

export default function ScheduleManager() {
    const [schedules, setSchedules] = useState<ComplianceSchedule[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);

    // Form state
    const [framework, setFramework] = useState('EU_AI_ACT');
    const [frequency, setFrequency] = useState('weekly');
    const [recipients, setRecipients] = useState('');

    useEffect(() => {
        fetchSchedules();
    }, []);

    const fetchSchedules = async () => {
        setLoading(true);
        try {
            const res = await complianceAutomationService.listSchedules();
            if (res.success && res.data) {
                setSchedules(res.data);
            }
        } catch (error) {
            console.error("Failed to fetch schedules", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        try {
            const recipientList = recipients.split(',').map(e => e.trim()).filter(e => e);
            const res = await complianceAutomationService.createSchedule({
                framework,
                frequency,
                recipients: recipientList
            });

            if (res.success) {
                setShowForm(false);
                setRecipients('');
                fetchSchedules();
            }
        } catch (error) {
            console.error("Failed to create schedule", error);
        }
    };

    return (
        <Card className="border-2 border-black shadow-brutal">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                    <IconCalendar />
                    Report Schedules
                </CardTitle>
                <Button size="sm" onClick={() => setShowForm(!showForm)} className="border-2 border-black">
                    <IconPlus size={16} className="mr-1" />
                    New Schedule
                </Button>
            </CardHeader>
            <CardContent className="space-y-4">
                {showForm && (
                    <div className="p-4 bg-gray-50 border-2 border-black rounded-lg space-y-4 mb-4">
                        <h4 className="font-bold">Create New Schedule</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Framework</label>
                                <Select value={framework} onValueChange={setFramework}>
                                    <SelectTrigger className="bg-white border-2 border-black">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="EU_AI_ACT">EU AI Act</SelectItem>
                                        <SelectItem value="GDPR">GDPR</SelectItem>
                                        <SelectItem value="DPDP">India DPDP</SelectItem>
                                        <SelectItem value="NIST_AI_RMF">NIST AI RMF</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Frequency</label>
                                <Select value={frequency} onValueChange={setFrequency}>
                                    <SelectTrigger className="bg-white border-2 border-black">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="daily">Daily</SelectItem>
                                        <SelectItem value="weekly">Weekly</SelectItem>
                                        <SelectItem value="monthly">Monthly</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Recipients (comma separated)</label>
                            <Input
                                value={recipients}
                                onChange={(e) => setRecipients(e.target.value)}
                                placeholder="email@example.com, team@example.com"
                                className="bg-white border-2 border-black"
                            />
                        </div>
                        <div className="flex justify-end gap-2">
                            <Button variant="neutral" onClick={() => setShowForm(false)}>Cancel</Button>
                            <Button onClick={handleCreate} className="border-2 border-black shadow-brutal">Save Schedule</Button>
                        </div>
                    </div>
                )}

                <div className="space-y-2">
                    {schedules.length === 0 && !loading ? (
                        <div className="text-center py-8 text-muted-foreground">
                            No active schedules found.
                        </div>
                    ) : (
                        schedules.map(schedule => (
                            <div key={schedule.id} className="flex items-center justify-between p-3 border-2 border-black rounded-lg bg-white hover:translate-x-1 transition-transform">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-bold">{schedule.framework}</span>
                                        <Badge variant="outline" className="capitalize">{schedule.frequency}</Badge>
                                    </div>
                                    <div className="text-sm text-muted-foreground mt-1">
                                        Recipients: {schedule.recipients.join(', ')}
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right text-xs text-muted-foreground">
                                        <div>Next: {schedule.next_run ? new Date(schedule.next_run).toLocaleDateString() : 'Pending'}</div>
                                        <div>Last: {schedule.last_run ? new Date(schedule.last_run).toLocaleDateString() : 'Never'}</div>
                                    </div>
                                    <Button variant="neutral" size="icon" className="text-red-500 hover:text-red-700 hover:bg-red-50">
                                        <IconTrash size={18} />
                                    </Button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
