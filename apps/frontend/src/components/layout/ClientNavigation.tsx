"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Header } from "./Header";
import { AppSidebar } from "./Sidebar";

interface ClientNavigationProps {
  children: React.ReactNode;
}

function MainContent({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* Full width header at top - fixed position across entire viewport */}
      <div className="fixed top-0 left-0 right-0 z-30 w-full">
        <Header onMenuToggle={() => { }} />
      </div>

      {/* Main content with sidebar offset */}
      <div
        className="flex flex-col flex-1 min-w-0 transition-[margin-left] duration-200 ease-linear"
        style={{
          marginTop: "68px", // Header height (64px h-16 + 4px border-bottom)
          paddingTop: 0,
        }}
      >
        <main className="flex-1 min-h-0 w-full overflow-auto bg-[#F3F5F0] px-3 pb-6 pt-3 sm:px-6">
          {children}
        </main>
      </div>
    </>
  );
}

export function ClientNavigation({ children }: ClientNavigationProps) {
  const pathname = usePathname();
  const isLegacyTestRoute = pathname === "/test" || pathname?.startsWith("/test/");
  const isAuthRoute =
    pathname?.startsWith("/login") ||
    pathname?.startsWith("/register") ||
    isLegacyTestRoute;


  // Keep only the singular legacy /test route shell-less. /tests is product navigation.
  if (isAuthRoute) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider>
      <div className="relative flex min-h-screen w-full overflow-x-clip">
        {/* Sidebar - fixed position, full height from top */}
        <AppSidebar />

        {/* Main content area - accounts for sidebar width dynamically */}
        <MainContent>{children}</MainContent>
      </div>
    </SidebarProvider>
  );
}
