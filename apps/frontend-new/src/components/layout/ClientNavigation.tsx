"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { SidebarProvider, useSidebar } from "@/components/ui/sidebar";
import { Header } from "./Header";
import { AppSidebar } from "./Sidebar";

interface ClientNavigationProps {
  children: React.ReactNode;
}

function MainContent({ children }: { children: React.ReactNode }) {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  // Sidebar width: 16rem when expanded, 3rem (48px) when collapsed
  const sidebarWidth = isCollapsed ? "3rem" : "16rem";

  return (
    <>
      {/* Full width header at top - fixed position across entire viewport */}
      <div className="fixed top-0 left-0 right-0 z-30 w-full">
        <Header onMenuToggle={() => {}} />
      </div>

      {/* Main content with sidebar offset */}
      <div
        className="flex flex-col flex-1 min-w-0 transition-[margin-left] duration-200 ease-linear"
        style={{
          marginLeft: sidebarWidth,
          marginTop: "68px", // Header height (64px h-16 + 4px border-bottom)
          paddingTop: 0,
        }}
      >
        <main className="flex-1 pt-3 pb-6 px-6 bg-gray-50 overflow-auto min-h-0 w-full">
          {children}
        </main>
      </div>
    </>
  );
}

export function ClientNavigation({ children }: ClientNavigationProps) {
  const pathname = usePathname();
  const isAuthRoute =
    pathname?.startsWith("/login") ||
    pathname?.startsWith("/register") ||
    pathname?.startsWith("/test");

  // Don't show sidebar/header on auth/test pages
  if (isAuthRoute) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full relative">
        {/* Sidebar - fixed position, full height from top */}
        <AppSidebar />

        {/* Main content area - accounts for sidebar width dynamically */}
        <MainContent>{children}</MainContent>
      </div>
    </SidebarProvider>
  );
}
