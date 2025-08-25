"use client"

import React from 'react';
import { OnboardingFlow } from '@/components/onboarding/onboarding-flow';

export default function OnboardingPage() {
  const handleComplete = () => {
    // Store that onboarding is completed
    localStorage.setItem('fairmind-onboarding-completed', 'true');
    console.log('Onboarding completed!');
  };

  const handleSkip = () => {
    // Store that onboarding was skipped
    localStorage.setItem('fairmind-onboarding-completed', 'true');
    localStorage.setItem('fairmind-onboarding-skipped', 'true');
    console.log('Onboarding skipped!');
  };

  return (
    <OnboardingFlow 
      onComplete={handleComplete}
      onSkip={handleSkip}
    />
  );
}
