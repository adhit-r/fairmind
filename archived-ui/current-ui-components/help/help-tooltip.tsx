"use client"

import React, { useState } from 'react';
import { HelpCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/common/button';

interface HelpTooltipProps {
  title: string;
  content: string | React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

export const HelpTooltip: React.FC<HelpTooltipProps> = ({
  title,
  content,
  position = 'top',
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2'
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
        aria-label="Help"
      >
        <HelpCircle className="w-3 h-3 text-gray-600 dark:text-gray-300" />
      </button>

      {isOpen && (
        <div className={`absolute z-50 ${positionClasses[position]}`}>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 max-w-xs">
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-semibold text-gray-900 dark:text-white text-sm">
                {title}
              </h4>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-300">
              {content}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface HelpSectionProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export const HelpSection: React.FC<HelpSectionProps> = ({
  title,
  children,
  className = ''
}) => {
  return (
    <div className={`bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 ${className}`}>
      <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center">
        <HelpCircle className="w-4 h-4 mr-2" />
        {title}
      </h3>
      <div className="text-sm text-blue-700 dark:text-blue-200">
        {children}
      </div>
    </div>
  );
};

interface QuickHelpProps {
  onShowOnboarding?: () => void;
  onShowDocumentation?: () => void;
  onShowSupport?: () => void;
}

export const QuickHelp: React.FC<QuickHelpProps> = ({
  onShowOnboarding,
  onShowDocumentation,
  onShowSupport
}) => {
  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
      <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-4 flex items-center">
        <HelpCircle className="w-5 h-5 mr-2" />
        Need Help?
      </h3>
      
      <div className="space-y-3">
        <button
          onClick={onShowOnboarding}
          className="w-full text-left p-3 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        >
          <div className="font-medium text-gray-900 dark:text-white">Take the Guided Tour</div>
          <div className="text-sm text-gray-600 dark:text-gray-300">Learn how to use FairMind step by step</div>
        </button>
        
        <button
          onClick={onShowDocumentation}
          className="w-full text-left p-3 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        >
          <div className="font-medium text-gray-900 dark:text-white">View Documentation</div>
          <div className="text-sm text-gray-600 dark:text-gray-300">Read detailed guides and tutorials</div>
        </button>
        
        <button
          onClick={onShowSupport}
          className="w-full text-left p-3 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        >
          <div className="font-medium text-gray-900 dark:text-white">Contact Support</div>
          <div className="text-sm text-gray-600 dark:text-gray-300">Get help from our support team</div>
        </button>
      </div>
    </div>
  );
};
