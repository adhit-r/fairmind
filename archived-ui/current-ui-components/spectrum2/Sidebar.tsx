import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface SidebarItem {
  label: string;
  href: string;
  icon?: React.ReactNode;
}

interface SidebarProps {
  items: SidebarItem[];
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  items,
  className = '',
}) => {
  const pathname = usePathname();

  return (
    <aside className={`spectrum-sidebar ${className}`}>
      <nav className="spectrum-sidebar-nav">
        <ul className="spectrum-nav-list">
          {items.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.href} className="spectrum-sidebar-item">
                <Link
                  href={item.href}
                  className={`spectrum-sidebar-link ${isActive ? 'active' : ''}`}
                >
                  {item.icon && (
                    <span className="mr-3">
                      {item.icon}
                    </span>
                  )}
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
};
