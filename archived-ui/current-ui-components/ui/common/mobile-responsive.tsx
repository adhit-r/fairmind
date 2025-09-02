import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from './button';
import { Card } from './card';
import { Menu, X, ChevronDown, ChevronUp } from 'lucide-react';

// Hook to detect mobile devices
export const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  return isMobile;
};

// Hook to detect touch devices
export const useIsTouch = () => {
  const [isTouch, setIsTouch] = useState(false);

  useEffect(() => {
    setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  return isTouch;
};

// Responsive container
interface ResponsiveContainerProps {
  children: React.ReactNode;
  className?: string;
  mobileClassName?: string;
  desktopClassName?: string;
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className,
  mobileClassName,
  desktopClassName,
}) => {
  const isMobile = useIsMobile();

  return (
    <div
      className={cn(
        className,
        isMobile ? mobileClassName : desktopClassName
      )}
    >
      {children}
    </div>
  );
};

// Mobile-friendly navigation menu
interface MobileNavProps {
  items: Array<{
    label: string;
    href: string;
    icon?: React.ReactNode;
    children?: Array<{
      label: string;
      href: string;
      icon?: React.ReactNode;
    }>;
  }>;
  className?: string;
}

export const MobileNav: React.FC<MobileNavProps> = ({ items, className }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  const toggleMenu = () => setIsOpen(!isOpen);

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  return (
    <div className={cn('relative', className)}>
      <Button
        onClick={toggleMenu}
        variant="outline"
        size="sm"
        className="md:hidden"
        aria-label="Toggle navigation menu"
        aria-expanded={isOpen}
      >
        {isOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
      </Button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50">
          <nav className="py-2">
            {items.map((item, index) => (
              <div key={index}>
                {item.children ? (
                  <div>
                    <button
                      onClick={() => toggleExpanded(index)}
                      className="w-full flex items-center justify-between px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                      <span className="flex items-center">
                        {item.icon && <span className="mr-2">{item.icon}</span>}
                        {item.label}
                      </span>
                      {expandedItems.has(index) ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                    {expandedItems.has(index) && (
                      <div className="pl-4 bg-gray-50 dark:bg-gray-800">
                        {item.children.map((child, childIndex) => (
                          <a
                            key={childIndex}
                            href={child.href}
                            className="flex items-center px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                            onClick={() => setIsOpen(false)}
                          >
                            {child.icon && <span className="mr-2">{child.icon}</span>}
                            {child.label}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <a
                    href={item.href}
                    className="flex items-center px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => setIsOpen(false)}
                  >
                    {item.icon && <span className="mr-2">{item.icon}</span>}
                    {item.label}
                  </a>
                )}
              </div>
            ))}
          </nav>
        </div>
      )}
    </div>
  );
};

// Mobile-friendly table
interface MobileTableProps {
  data: Array<Record<string, any>>;
  columns: Array<{
    key: string;
    label: string;
    render?: (value: any, row: any) => React.ReactNode;
  }>;
  className?: string;
}

export const MobileTable: React.FC<MobileTableProps> = ({
  data,
  columns,
  className,
}) => {
  const isMobile = useIsMobile();

  if (isMobile) {
    return (
      <div className={cn('space-y-4', className)}>
        {data.map((row, rowIndex) => (
          <Card key={rowIndex} className="p-4">
            {columns.map((column) => (
              <div key={column.key} className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0">
                <span className="font-medium text-gray-600 dark:text-gray-400">
                  {column.label}:
                </span>
                <span className="text-right">
                  {column.render ? column.render(row[column.key], row) : row[column.key]}
                </span>
              </div>
            ))}
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-2 text-left border-b">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-2 border-b">
                  {column.render ? column.render(row[column.key], row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Mobile-friendly form layout
interface MobileFormProps {
  children: React.ReactNode;
  className?: string;
  columns?: number;
}

export const MobileForm: React.FC<MobileFormProps> = ({
  children,
  className,
  columns = 2,
}) => {
  const isMobile = useIsMobile();

  return (
    <div
      className={cn(
        'space-y-4',
        isMobile ? 'space-y-4' : `grid grid-cols-${columns} gap-4`,
        className
      )}
    >
      {children}
    </div>
  );
};

// Mobile-friendly card grid
interface MobileCardGridProps {
  children: React.ReactNode;
  className?: string;
  columns?: number;
}

export const MobileCardGrid: React.FC<MobileCardGridProps> = ({
  children,
  className,
  columns = 3,
}) => {
  const isMobile = useIsMobile();

  return (
    <div
      className={cn(
        'space-y-4',
        isMobile 
          ? 'space-y-4' 
          : `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-${columns} gap-4`,
        className
      )}
    >
      {children}
    </div>
  );
};

// Mobile-friendly modal/dialog
interface MobileModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  className?: string;
}

export const MobileModal: React.FC<MobileModalProps> = ({
  isOpen,
  onClose,
  children,
  title,
  className,
}) => {
  const isMobile = useIsMobile();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      <Card
        className={cn(
          'relative w-full max-w-md max-h-[90vh] overflow-y-auto',
          isMobile ? 'mx-4' : '',
          className
        )}
      >
        {title && (
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">{title}</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              aria-label="Close modal"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}
        <div className="p-4">{children}</div>
      </Card>
    </div>
  );
};

// Mobile-friendly bottom sheet
interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  className?: string;
}

export const BottomSheet: React.FC<BottomSheetProps> = ({
  isOpen,
  onClose,
  children,
  title,
  className,
}) => {
  const isMobile = useIsMobile();

  if (!isMobile || !isOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      <div className="absolute bottom-0 left-0 right-0 bg-white dark:bg-gray-900 rounded-t-lg shadow-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            aria-label="Close bottom sheet"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
        <div className={cn('p-4 max-h-[70vh] overflow-y-auto', className)}>
          {children}
        </div>
      </div>
    </div>
  );
};
