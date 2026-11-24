/// <reference path="../.astro/types.d.ts" />

interface Window {
  fairmindConsent: {
    setConsent(choice: { analytics: boolean; source: string; policyVersion: string }): void;
  };
}
