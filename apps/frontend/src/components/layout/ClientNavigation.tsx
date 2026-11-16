"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { SidebarProvider } from "@/components/ui/sidebar";
import { OrgProvider } from "@/context/OrgContext";
import { SessionProvider, useSession } from "@/context/SessionContext";
import { Header } from "./Header";
import { AppSidebar } from "./Sidebar";

interface ClientNavigationProps {
  children: React.ReactNode;
}

/** Organization data is only fetched once a session exists. */
function AuthenticatedProviders({ children }: { children: React.ReactNode }) {
  const { status } = useSession();
  if (status !== "authenticated") return <>{children}</>;
  return <OrgProvider>{children}</OrgProvider>;
}

export function ClientNavigation({ children }: ClientNavigationProps) {
  const pathname = usePathname();
  const isLegacyTestRoute = pathname === "/test" || pathname?.startsWith("/test/");
  const isAuthRoute =
    pathname?.startsWith("/login") ||
    pathname?.startsWith("/register") ||
    pathname?.startsWith("/callback") ||
    pathname?.startsWith("/invitations/") ||
    isLegacyTestRoute;

  // Auth screens render without the product shell. (/test, the singular legacy route, is shell-less too.)
  if (isAuthRoute) {
    return <>{children}</>;
  }

  return (
    <SessionProvider>
      <AuthenticatedProviders>
        <SidebarProvider className="flex-col">
          <a
            href="#main-content"
            className="sr-only z-50 rounded-md bg-card px-4 py-2 text-sm font-medium text-foreground shadow-sm focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
          >
            Skip to main content
          </a>
          <Header />
          <div className="flex min-h-0 w-full min-w-0 flex-1">
            <AppSidebar />
            <main
              id="main-content"
              tabIndex={-1}
              className="min-w-0 flex-1 bg-background px-4 pb-10 pt-5 outline-none sm:px-6 lg:px-8"
            >
              <div className="mx-auto w-full max-w-[1400px]">{children}</div>
            </main>
          </div>
        </SidebarProvider>
      </AuthenticatedProviders>
    </SessionProvider>
  );
}
