"use client"

import { Home, Plus, History, Settings, HelpCircle, Shield, Brain, FileText, Users, AlertTriangle } from "lucide-react"
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

const governanceItems = [
  {
    title: "DASHBOARD",
    url: "/",
    icon: Home,
  },
  {
    title: "AI_GOVERNANCE",
    url: "/governance",
    icon: Shield,
  },
  {
    title: "MODEL_REGISTRY",
    url: "/models",
    icon: Brain,
  },
  {
    title: "RISK_ASSESSMENT",
    url: "/risk",
    icon: AlertTriangle,
  },
]

const testingItems = [
  {
    title: "NEW_SIMULATION",
    url: "/simulation/new",
    icon: Plus,
  },
  {
    title: "SIMULATION_HISTORY",
    url: "/history",
    icon: History,
  },
  {
    title: "LLM_TESTING",
    url: "/llm",
    icon: Brain,
  },
]

const complianceItems = [
  {
    title: "AUDIT_LOGS",
    url: "/audit",
    icon: FileText,
  },
  {
    title: "STAKEHOLDERS",
    url: "/stakeholders",
    icon: Users,
  },
]

const settingsItems = [
  {
    title: "SETTINGS",
    url: "/settings",
    icon: Settings,
  },
  {
    title: "HELP_&_SUPPORT",
    url: "/help",
    icon: HelpCircle,
  },
]

export function AppSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <Sidebar variant="inset" collapsible="icon" onCollapsedChange={setIsCollapsed}>
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
            {isCollapsed ? "GOV" : "GOVERNANCE"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {governanceItems.map((item) => (
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
            {isCollapsed ? "TEST" : "TESTING"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {testingItems.map((item) => (
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
            {isCollapsed ? "COMP" : "COMPLIANCE"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {complianceItems.map((item) => (
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
            {isCollapsed ? "SYS" : "SYSTEM"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsItems.map((item) => (
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
