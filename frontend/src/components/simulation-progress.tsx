"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Clock, XCircle } from "lucide-react"
import Link from "next/link"
import io from 'socket.io-client';

interface Step {
  id: number;
  name: string;
  status: string;
}

interface ProgressData {
  progress: number;
}

export function SimulationProgress() {
  const [progress, setProgress] = useState(0);
  const [steps, setSteps] = useState<Step[]>([]);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const socket = io('http://localhost:3001');

    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    socket.on('progress', (data: ProgressData) => {
      setProgress(data.progress);
    });

    socket.on('steps', (data: Step[]) => {
      setSteps(data);
    });

    socket.on('log', (data: string) => {
      setLogs((prevLogs) => [...prevLogs, data]);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "in-progress":
        return <Clock className="h-4 w-4 text-blue-600 animate-spin" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/30" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-green-100 text-green-800">✅</Badge>
      case "in-progress":
        return <Badge className="bg-blue-100 text-blue-800">⏳</Badge>
      case "failed":
        return <Badge className="bg-red-100 text-red-800">❌</Badge>
      default:
        return <Badge variant="outline">⏸️</Badge>
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">SIMULATION_IN_PROGRESS</h1>
        <p className="text-sm text-muted-foreground font-mono">TESTING.LOAN_MODEL_V1.FOR.ETHICAL.RISKS</p>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Overall Progress</CardTitle>
              <CardDescription>{Math.round(progress)}% complete • Estimated time remaining: ~7 minutes</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">{Math.round(progress)}%</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={progress} className="w-full h-3" />
        </CardContent>
      </Card>

      {/* Live Status */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Progress Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Progress Steps</CardTitle>
            <CardDescription>Current simulation pipeline status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center gap-3">
                  {getStatusIcon(step.status)}
                  <div className="flex-1">
                    <p
                      className={`text-sm ${
                        step.status === "completed"
                          ? "text-muted-foreground"
                          : step.status === "in-progress"
                            ? "font-medium"
                            : "text-muted-foreground"
                      }`}
                    >
                      {step.name}
                    </p>
                  </div>
                  {getStatusBadge(step.status)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Live Logs */}
        <Card>
          <CardHeader>
            <CardTitle>Live Logs</CardTitle>
            <CardDescription>Real-time simulation output</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="terminal p-4 rounded-md text-xs space-y-1 h-64 overflow-y-auto">
              {logs.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Current Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Preliminary Results</CardTitle>
          <CardDescription>Early insights from completed tests</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium">Synthetic Data Quality</span>
              </div>
              <div className="text-2xl font-bold text-green-600">95%</div>
              <p className="text-xs text-muted-foreground">High fidelity scenarios generated</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 bg-yellow-500 rounded-full"></div>
                <span className="text-sm font-medium">Fairness Score (Partial)</span>
              </div>
              <div className="text-2xl font-bold text-yellow-600">78%</div>
              <p className="text-xs text-muted-foreground">Some bias detected, analysis ongoing</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 bg-gray-400 rounded-full"></div>
                <span className="text-sm font-medium">Robustness Score</span>
              </div>
              <div className="text-2xl font-bold text-gray-600">--</div>
              <p className="text-xs text-muted-foreground">Testing not yet started</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <Link href="/">
          <Button variant="outline" className="text-xs bg-transparent">
            BACK_TO_DASHBOARD
          </Button>
        </Link>

        <div className="flex gap-2">
          <Button variant="destructive" size="sm" className="text-xs">
            CANCEL_SIMULATION
          </Button>
          {progress >= 100 && (
            <Link href="/simulation/1/results">
              <Button className="bg-white text-black hover:bg-gray-200 text-xs">VIEW_RESULTS</Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
