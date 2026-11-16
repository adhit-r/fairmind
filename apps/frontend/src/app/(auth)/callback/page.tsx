/**
 * OAuth2 Callback Handler Page
 *
 * This page handles the redirect from Authentik after user authentication.
 * Exchanges the authorization code for tokens and redirects to dashboard.
 */

"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { IconAlertTriangle } from "@tabler/icons-react";
import { AuthShell } from "@/components/auth/AuthShell";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthentik } from "@/lib/api/hooks/useAuthentik";

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<AuthCallbackLoading />}>
      <AuthCallbackContent />
    </Suspense>
  );
}

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { handleCallback } = useAuthentik();

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Extract authorization code and state from URL
        const code = searchParams.get("code");
        const state = searchParams.get("state");
        const errorParam = searchParams.get("error");
        const errorDescription = searchParams.get("error_description");

        // Check for OAuth2 errors
        if (errorParam) {
          const errorMessage = `Authentication failed: ${errorParam}${
            errorDescription ? ` - ${errorDescription}` : ""
          }`;
          console.error(errorMessage);
          setError(errorMessage);
          return;
        }

        // Validate required parameters
        if (!code || !state) {
          const missingParams = [];
          if (!code) missingParams.push("code");
          if (!state) missingParams.push("state");
          const errorMessage = `Missing required OAuth2 parameters: ${missingParams.join(", ")}`;
          console.error(errorMessage);
          setError(errorMessage);
          return;
        }

        // Exchange code for tokens
        await handleCallback(code, state);
        // handleCallback redirects on success
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error occurred";
        console.error("OAuth2 callback error:", err);
        setError(errorMessage);
      }
    };

    processCallback();
  }, [searchParams, handleCallback]);

  if (error) {
    return (
      <AuthShell title="Sign-in could not be completed">
        <Alert variant="destructive" className="mb-5">
          <IconAlertTriangle aria-hidden="true" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button className="w-full" onClick={() => router.push("/login")}>
          Back to sign in
        </Button>
      </AuthShell>
    );
  }

  return <AuthCallbackLoading />;
}

function AuthCallbackLoading() {
  return (
    <AuthShell title="Completing sign-in" description="Please wait while we verify your account.">
      <div role="status" aria-live="polite" className="space-y-3">
        <span className="sr-only">Completing sign-in</span>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </AuthShell>
  );
}
