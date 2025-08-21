import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from './button';
import { Card } from './card';
import { 
  SkipForward, 
  Volume2, 
  VolumeX, 
  Eye, 
  EyeOff, 
  Keyboard,
  Accessibility,
  HelpCircle
} from 'lucide-react';

// Skip to main content link
export const SkipToMainContent: React.FC = () => {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium shadow-lg"
    >
      Skip to main content
    </a>
  );
};

// Focus trap for modals and dialogs
interface FocusTrapProps {
  children: React.ReactNode;
  active?: boolean;
  className?: string;
}

export const FocusTrap: React.FC<FocusTrapProps> = ({
  children,
  active = true,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [focusableElements, setFocusableElements] = useState<HTMLElement[]>([]);

  useEffect(() => {
    if (!active || !containerRef.current) return;

    const container = containerRef.current;
    const elements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;
    
    setFocusableElements(Array.from(elements));

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [active, focusableElements]);

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  );
};

// Accessibility menu component
interface AccessibilityMenuProps {
  className?: string;
}

export const AccessibilityMenu: React.FC<AccessibilityMenuProps> = ({
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [fontSize, setFontSize] = useState(16);

  const toggleMenu = () => setIsOpen(!isOpen);

  const toggleHighContrast = () => {
    setHighContrast(!highContrast);
    document.documentElement.classList.toggle('high-contrast');
  };

  const toggleReducedMotion = () => {
    setReducedMotion(!reducedMotion);
    document.documentElement.classList.toggle('reduced-motion');
  };

  const increaseFontSize = () => {
    const newSize = Math.min(fontSize + 2, 24);
    setFontSize(newSize);
    document.documentElement.style.fontSize = `${newSize}px`;
  };

  const decreaseFontSize = () => {
    const newSize = Math.max(fontSize - 2, 12);
    setFontSize(newSize);
    document.documentElement.style.fontSize = `${newSize}px`;
  };

  const resetFontSize = () => {
    setFontSize(16);
    document.documentElement.style.fontSize = '16px';
  };

  return (
    <div className={cn('relative', className)}>
      <Button
        onClick={toggleMenu}
        variant="outline"
        size="sm"
        aria-label="Accessibility options"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <Accessibility className="w-4 h-4 mr-2" />
        Accessibility
      </Button>

      {isOpen && (
        <FocusTrap>
          <Card className="absolute top-full right-0 mt-2 w-80 p-4 z-50 shadow-lg">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium">Accessibility Options</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleMenu}
                  aria-label="Close accessibility menu"
                >
                  ×
                </Button>
              </div>

              <div className="space-y-3">
                {/* High Contrast */}
                <div className="flex items-center justify-between">
                  <label className="text-sm flex items-center">
                    <Eye className="w-4 h-4 mr-2" />
                    High Contrast
                  </label>
                  <Button
                    variant={highContrast ? "default" : "outline"}
                    size="sm"
                    onClick={toggleHighContrast}
                    aria-pressed={highContrast}
                  >
                    {highContrast ? "On" : "Off"}
                  </Button>
                </div>

                {/* Reduced Motion */}
                <div className="flex items-center justify-between">
                  <label className="text-sm flex items-center">
                    <SkipForward className="w-4 h-4 mr-2" />
                    Reduced Motion
                  </label>
                  <Button
                    variant={reducedMotion ? "default" : "outline"}
                    size="sm"
                    onClick={toggleReducedMotion}
                    aria-pressed={reducedMotion}
                  >
                    {reducedMotion ? "On" : "Off"}
                  </Button>
                </div>

                {/* Font Size */}
                <div className="space-y-2">
                  <label className="text-sm flex items-center">
                    <Keyboard className="w-4 h-4 mr-2" />
                    Font Size
                  </label>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={decreaseFontSize}
                      aria-label="Decrease font size"
                    >
                      A-
                    </Button>
                    <span className="text-sm min-w-[2rem] text-center">
                      {fontSize}px
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={increaseFontSize}
                      aria-label="Increase font size"
                    >
                      A+
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={resetFontSize}
                      aria-label="Reset font size"
                    >
                      Reset
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </FocusTrap>
      )}
    </div>
  );
};

// Screen reader only text
export const SrOnly: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <span className="sr-only">{children}</span>;
};

// Visually hidden but accessible to screen readers
export const VisuallyHidden: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <span
      className="absolute w-px h-px p-0 -m-px overflow-hidden whitespace-nowrap border-0"
      style={{ clip: 'rect(0, 0, 0, 0)' }}
    >
      {children}
    </span>
  );
};

// Live region for announcements
interface LiveRegionProps {
  children: React.ReactNode;
  className?: string;
  'aria-live'?: 'polite' | 'assertive' | 'off';
  'aria-atomic'?: boolean;
}

export const LiveRegion: React.FC<LiveRegionProps> = ({
  children,
  className,
  'aria-live': ariaLive = 'polite',
  'aria-atomic': ariaAtomic = true,
}) => {
  return (
    <div
      className={cn('sr-only', className)}
      aria-live={ariaLive}
      aria-atomic={ariaAtomic}
    >
      {children}
    </div>
  );
};

// Keyboard navigation hook
export const useKeyboardNavigation = (
  items: any[],
  onSelect?: (item: any, index: number) => void
) => {
  const [focusedIndex, setFocusedIndex] = useState(-1);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex(prev => 
          prev < items.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex(prev => 
          prev > 0 ? prev - 1 : items.length - 1
        );
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (focusedIndex >= 0 && onSelect) {
          onSelect(items[focusedIndex], focusedIndex);
        }
        break;
      case 'Escape':
        setFocusedIndex(-1);
        break;
    }
  };

  return {
    focusedIndex,
    setFocusedIndex,
    handleKeyDown,
  };
};

// Accessibility provider for global settings
interface AccessibilityContextType {
  highContrast: boolean;
  reducedMotion: boolean;
  fontSize: number;
  setHighContrast: (value: boolean) => void;
  setReducedMotion: (value: boolean) => void;
  setFontSize: (size: number) => void;
}

const AccessibilityContext = React.createContext<AccessibilityContextType | undefined>(undefined);

export const AccessibilityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [highContrast, setHighContrast] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [fontSize, setFontSize] = useState(16);

  const value = {
    highContrast,
    reducedMotion,
    fontSize,
    setHighContrast,
    setReducedMotion,
    setFontSize,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = () => {
  const context = React.useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};
