"use client"

import { Home, Plus, History, Settings, HelpCircle, Shield, Brain, FileText, Users, AlertTriangle, Info } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useState } from "react"

// Sidebar taxonomy: Analyze, Monitor, Explain, Govern, Simulate
const analyzeItems = [
  { title: "DASHBOARD", url: "/", icon: Home },
  { title: "BIAS_DETECTION", url: "/bias-detection", icon: AlertTriangle },
  { title: "MODEL_DNA", url: "/model-dna", icon: Brain },
  { title: "KNOWLEDGE_GRAPH", url: "/knowledge-graph", icon: FileText },
  { title: "LLM_TESTING", url: "/llm-testing", icon: Brain },
]

const monitorItems = [
  { title: "MONITORING", url: "/monitoring", icon: Shield },
  { title: "ANALYTICS", url: "/analytics", icon: FileText },
  { title: "GEOGRAPHIC_BIAS", url: "/geographic-bias", icon: AlertTriangle },
]

const explainItems = [
  { title: "HOW_IT_WORKS", url: "/how-it-works", icon: Info },
  { title: "AI_ETHICS_OBSERVATORY", url: "/ai-ethics-observatory", icon: Brain },
  { title: "HELP_&_SUPPORT", url: "/help", icon: HelpCircle },
]

const governItems = [
  { title: "COMPLIANCE", url: "/compliance", icon: Shield },
  { title: "AUDIT_LOGS", url: "/audit-logs", icon: FileText },
  { title: "STAKEHOLDERS", url: "/stakeholders", icon: Users },
  { title: "SETTINGS", url: "/settings", icon: Settings },
]

const simulateItems = [
  { title: "NEW_SIMULATION", url: "/simulation", icon: Plus },
  { title: "SIMULATION_HISTORY", url: "/simulation-history", icon: History },
  { title: "MODEL_INVENTORY", url: "/models", icon: Brain },
  { title: "MODEL_UPLOAD", url: "/model-upload", icon: FileText },
]

export function AppSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <Sidebar variant="inset" collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-3 px-2 py-4">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-white text-black font-bold">
            <span className="text-sm">FM</span>
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-wider">FAIRMIND</span>
              <span className="text-xs text-muted-foreground tracking-wide">AI.GOVERNANCE.PLATFORM</span>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-bold tracking-wider">
            {isCollapsed ? "ANZ" : "ANALYZE"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {analyzeItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className="font-mono text-sm">
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      {!isCollapsed && <span className="tracking-wide">{item.title}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-bold tracking-wider">
            {isCollapsed ? "MON" : "MONITOR"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {monitorItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className="font-mono text-sm">
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      {!isCollapsed && <span className="tracking-wide">{item.title}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-bold tracking-wider">
            {isCollapsed ? "EXP" : "EXPLAIN"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {explainItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className="font-mono text-sm">
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      {!isCollapsed && <span className="tracking-wide">{item.title}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-bold tracking-wider">
            {isCollapsed ? "GOV" : "GOVERN"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {governItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className="font-mono text-sm">
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      {!isCollapsed && <span className="tracking-wide">{item.title}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-bold tracking-wider">
            {isCollapsed ? "SIM" : "SIMULATE"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {simulateItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className="font-mono text-sm">
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      {!isCollapsed && <span className="tracking-wide">{item.title}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton className="font-mono">
              <Avatar className="h-6 w-6">
                <AvatarImage src="/placeholder.svg?height=24&width=24" />
                <AvatarFallback className="text-xs font-bold">JD</AvatarFallback>
              </Avatar>
              {!isCollapsed && <span className="tracking-wide">JOHN.DOE</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
} 