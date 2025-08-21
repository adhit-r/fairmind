import React, { useState, useEffect, useRef, useCallback, useMemo, Suspense } from 'react';
import { cn } from '@/lib/utils';
import { Skeleton } from './loading-skeleton';

// Lazy loading component with intersection observer
interface LazyLoadProps {
  children: React.ReactNode;
  placeholder?: React.ReactNode;
  threshold?: number;
  className?: string;
}

export const LazyLoad: React.FC<LazyLoadProps> = ({
  children,
  placeholder = <Skeleton className="w-full h-32" />,
  threshold = 0.1,
  className,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [threshold]);

  useEffect(() => {
    if (isVisible) {
      // Simulate loading delay for better UX
      const timer = setTimeout(() => setIsLoaded(true), 100);
      return () => clearTimeout(timer);
    }
  }, [isVisible]);

  return (
    <div ref={ref} className={className}>
      {!isLoaded ? placeholder : children}
    </div>
  );
};

// Virtualized list for large datasets
interface VirtualizedListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
}

export function VirtualizedList<T>({
  items,
  height,
  itemHeight,
  renderItem,
  className,
}: VirtualizedListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const visibleItemCount = Math.ceil(height / itemHeight);
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(startIndex + visibleItemCount + 1, items.length);

  const visibleItems = items.slice(startIndex, endIndex);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn('overflow-auto', className)}
      style={{ height }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div key={startIndex + index} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Memoized component wrapper
export function withMemo<T extends object>(
  Component: React.ComponentType<T>,
  propsAreEqual?: (prevProps: T, nextProps: T) => boolean
) {
  return React.memo(Component, propsAreEqual);
}

// Debounced input component
interface DebouncedInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  delay?: number;
  className?: string;
}

export const DebouncedInput: React.FC<DebouncedInputProps> = ({
  value,
  onChange,
  placeholder,
  delay = 300,
  className,
}) => {
  const [localValue, setLocalValue] = useState(value);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = event.target.value;
      setLocalValue(newValue);

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        onChange(newValue);
      }, delay);
    },
    [onChange, delay]
  );

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <input
      type="text"
      value={localValue}
      onChange={handleChange}
      placeholder={placeholder}
      className={cn(
        'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white',
        className
      )}
    />
  );
};

// Image optimization component
interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  placeholder?: string;
  lazy?: boolean;
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  className,
  placeholder,
  lazy = true,
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const handleLoad = () => setIsLoaded(true);
  const handleError = () => setHasError(true);

  if (hasError) {
    return (
      <div
        className={cn(
          'flex items-center justify-center bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
          className
        )}
        style={{ width, height }}
      >
        <span className="text-sm">Image failed to load</span>
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      {!isLoaded && placeholder && (
        <div
          className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse"
          style={{ width, height }}
        />
      )}
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading={lazy ? 'lazy' : 'eager'}
        onLoad={handleLoad}
        onError={handleError}
        className={cn(
          'transition-opacity duration-300',
          isLoaded ? 'opacity-100' : 'opacity-0'
        )}
      />
    </div>
  );
};

// Performance monitoring hook
export const usePerformanceMonitor = (componentName: string) => {
  const renderCount = useRef(0);
  const lastRenderTime = useRef(performance.now());

  useEffect(() => {
    renderCount.current += 1;
    const currentTime = performance.now();
    const timeSinceLastRender = currentTime - lastRenderTime.current;
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`${componentName} render #${renderCount.current} (${timeSinceLastRender.toFixed(2)}ms)`);
    }
    
    lastRenderTime.current = currentTime;
  });

  return {
    renderCount: renderCount.current,
  };
};

// Code splitting wrapper
export const withCodeSplitting = <T extends object>(
  importFn: () => Promise<{ default: React.ComponentType<T> }>,
  fallback?: React.ReactNode
) => {
  const LazyComponent = React.lazy(importFn);
  
  return (props: T) => (
    <Suspense fallback={fallback || <Skeleton className="w-full h-32" />}>
      <LazyComponent {...props} />
    </Suspense>
  );
};

// Infinite scroll hook
export const useInfiniteScroll = (
  callback: () => void,
  hasMore: boolean,
  threshold = 100
) => {
  const [isLoading, setIsLoading] = useState(false);
  const observerRef = useRef<IntersectionObserver>();

  const lastElementRef = useCallback(
    (node: HTMLElement | null) => {
      if (isLoading) return;
      
      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      observerRef.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && hasMore) {
            setIsLoading(true);
            callback();
          }
        },
        { rootMargin: `${threshold}px` }
      );

      if (node) {
        observerRef.current.observe(node);
      }
    },
    [callback, hasMore, isLoading, threshold]
  );

  useEffect(() => {
    setIsLoading(false);
  }, [callback]);

  return { lastElementRef, isLoading };
};

// Throttled scroll hook
export const useThrottledScroll = (callback: () => void, delay = 100) => {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const lastRun = useRef(0);

  const throttledCallback = useCallback(() => {
    const now = Date.now();
    
    if (lastRun.current && now - lastRun.current < delay) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        lastRun.current = now;
        callback();
      }, delay - (now - lastRun.current));
    } else {
      lastRun.current = now;
      callback();
    }
  }, [callback, delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return throttledCallback;
};

// Memory efficient list rendering
interface EfficientListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T, index: number) => string | number;
  className?: string;
  batchSize?: number;
}

export function EfficientList<T>({
  items,
  renderItem,
  keyExtractor,
  className,
  batchSize = 50,
}: EfficientListProps<T>) {
  const [visibleCount, setVisibleCount] = useState(batchSize);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisibleCount(items.length);
    }, 100);

    return () => clearTimeout(timer);
  }, [items.length]);

  const visibleItems = items.slice(0, visibleCount);

  return (
    <div className={className}>
      {visibleItems.map((item, index) => (
        <div key={keyExtractor(item, index)}>
          {renderItem(item, index)}
        </div>
      ))}
    </div>
  );
}
