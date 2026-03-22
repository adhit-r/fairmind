/**
 * OAuth2 Callback Handler Page
 *
 * This page handles the redirect from Authentik after user authentication.
 * Exchanges the authorization code for tokens and redirects to dashboard.
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthentik } from "@/lib/api/hooks/useAuthentik";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { handleCallback } = useAuthentik();

  const [isProcessing, setIsProcessing] = useState(true);
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
          setIsProcessing(false);
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
          setIsProcessing(false);
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
        setIsProcessing(false);
      }
    };

    processCallback();
  }, [searchParams, handleCallback]);

  // Show error state
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="w-full max-w-md rounded-lg border-4 border-black bg-white p-8 shadow-brutal-lg">
          <h1 className="mb-4 text-2xl font-bold text-black">
            Authentication Error
          </h1>
          <p className="mb-6 text-gray-700">{error}</p>
          <button
            onClick={() => router.push("/auth/login")}
            className="w-full rounded-lg bg-black px-4 py-2 font-bold text-white transition-all hover:shadow-brutal-lg"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  // Show loading state while processing
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-md rounded-lg border-4 border-black bg-white p-8 shadow-brutal-lg">
        <h1 className="mb-4 text-2xl font-bold text-black">
          Completing Authentication
        </h1>
        <p className="mb-6 text-gray-700">
          Please wait while we process your authentication...
        </p>

        {/* Loading spinner */}
        <div className="flex justify-center">
          <div
            className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black"
            role="status"
            aria-label="Loading"
          />
        </div>

        {isProcessing && (
          <p className="mt-4 text-center text-sm text-gray-600">
            Redirecting to dashboard...
          </p>
        )}
      </div>
    </div>
  );
}
