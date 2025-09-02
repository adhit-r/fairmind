import React from 'react';

interface TabItem {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

interface TabsProps {
  value: string;
  onValueChange: (value: string) => void;
  items: TabItem[];
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  value,
  onValueChange,
  items,
  className = '',
}) => {
  return (
    <div className={`spectrum-tabs ${className}`}>
      <div className="spectrum-tabList">
        {items.map((item) => (
          <button
            key={item.value}
            className={`spectrum-tab ${value === item.value ? 'spectrum-tab--selected' : ''}`}
            onClick={() => onValueChange(item.value)}
          >
            {item.icon && <span className="spectrum-tab-icon">{item.icon}</span>}
            <span className="spectrum-tab-label">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

interface TabContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export const TabContent: React.FC<TabContentProps> = ({
  value,
  children,
  className = '',
}) => {
  return (
    <div className={`spectrum-tabPanel ${className}`}>
      {children}
    </div>
  );
};
