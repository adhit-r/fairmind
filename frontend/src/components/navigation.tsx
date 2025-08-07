'use client';

import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/auth-context';
import { Button } from './ui';
import { useState, useRef } from 'react';
import { useButton } from '@react-aria/button';
import { useFocusRing } from '@react-aria/focus';
import { useMenuTrigger } from '@react-aria/menu';
import { useMenuTriggerState } from '@react-stately/menu';
import { OverlayContainer } from '@react-aria/overlays';
import { XCircle, ChevronDown } from 'lucide-react';

export function Navigation() {
  const { user, profile, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  
  const menuState = useMenuTriggerState({ isOpen, onOpenChange: setIsOpen });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const { menuTriggerProps, menuProps } = useMenuTrigger({}, menuState, triggerRef);
  const { buttonProps } = useButton({
    ...menuTriggerProps,
    onPress: () => setIsOpen(!isOpen),
  }, triggerRef);
  
  const { focusProps } = useFocusRing();
  
  const navItems = [
    { name: 'Dashboard', href: '/dashboard', requiresAuth: true },
    { name: 'Simulations', href: '/simulations', requiresAuth: true },
    { name: 'Documentation', href: '/docs', requiresAuth: false },
  ];

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (pathname === '/login') return null;

  return (
    <header className="border-b border-gray-200 dark:border-gray-700">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" aria-label="Top">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <span className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                FairMind
              </span>
            </Link>
            
            <div className="hidden md:ml-10 md:block">
              <div className="flex space-x-8">
                {navItems.map((item) => {
                  if (item.requiresAuth && !user) return null;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`text-sm font-medium ${
                        isActive 
                          ? 'text-indigo-600 dark:text-indigo-400' 
                          : 'text-gray-700 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400'
                      }`}
                    >
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="relative">
                <button
                  {...buttonProps}
                  {...focusProps}
                  className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400"
                >
                  <span className="truncate">{profile?.full_name || user.email}</span>
                  <span className="ml-1.5 flex-shrink-0 rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200">
                    {user.role}
                  </span>
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                </button>
                
                {isOpen ? (OverlayContainer({
                  children: (() => {
                    const { autoFocus, ...divMenuProps } = menuProps;
                    return (
                      <div
                        className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none dark:bg-gray-800 dark:ring-gray-700"
                        {...divMenuProps}
                      >
                        <Link
                          href="/profile"
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                          onClick={() => setIsOpen(false)}
                        >
                          Your Profile
                        </Link>
                        <Link
                          href="/settings"
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                          onClick={() => setIsOpen(false)}
                        >
                          Settings
                        </Link>
                        <button
                          onClick={handleLogout}
                          className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                        >
                          Sign out
                        </button>
                      </div>
                    );
                  })()
                }) as unknown as React.ReactNode) : null}
              </div>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm font-medium text-gray-700 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400"
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="ml-8 inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
}
