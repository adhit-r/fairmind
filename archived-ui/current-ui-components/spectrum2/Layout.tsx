import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  Upload, 
  TestTube, 
  Shield, 
  FileText, 
  Settings, 
  Search, 
  Bell, 
  User, 
  HelpCircle, 
  LogOut,
  Menu,
  X,
  ChevronDown,
  ChevronRight,
  Database,
  BarChart3,
  Users,
  Lock,
  AlertTriangle,
  CheckCircle,
  Clock,
  Star,
  Folder,
  Grid,
  List,
  Filter,
  Download,
  MoreHorizontal,
  Plus,
  Eye,
  Edit,
  Trash2,
  Copy,
  Share,
  Archive,
  RefreshCw,
  Zap,
  Target,
  TrendingUp,
  Activity,
  Globe,
  Key,
  Shield as ShieldIcon,
  FileCheck,
  AlertCircle,
  Info,
  ExternalLink
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  id: string;
  name: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  badgeColor?: 'default' | 'success' | 'warning' | 'error';
  children?: NavigationItem[];
  description?: string;
}

interface NavigationSection {
  id: string;
  title: string;
  items: NavigationItem[];
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<string[]>(['main']);
  const pathname = usePathname();

  const navigationSections: NavigationSection[] = [
    {
      id: 'main',
      title: 'Main',
      items: [
        { 
          id: 'dashboard',
          name: 'Dashboard', 
          href: '/', 
          icon: <Home size={20} />,
          description: 'Overview and key metrics'
        },
        { 
          id: 'models',
          name: 'Models', 
          href: '/models', 
          icon: <Database size={20} />,
          badge: '24',
          badgeColor: 'default',
          description: 'AI model management'
        },
        { 
          id: 'analytics',
          name: 'Analytics', 
          href: '/analytics', 
          icon: <BarChart3 size={20} />,
          description: 'Performance insights'
        },
      ]
    },
    {
      id: 'governance',
      title: 'Governance',
      items: [
        { 
          id: 'bias-detection',
          name: 'Bias Detection', 
          href: '/bias-detection', 
          icon: <Shield size={20} />,
          badge: '3',
          badgeColor: 'warning',
          description: 'Fairness analysis'
        },
        { 
          id: 'compliance',
          name: 'Compliance', 
          href: '/compliance', 
          icon: <FileCheck size={20} />,
          description: 'Regulatory compliance'
        },
        { 
          id: 'security',
          name: 'Security', 
          href: '/security', 
          icon: <Lock size={20} />,
          description: 'Security monitoring'
        },
        { 
          id: 'ai-bom',
          name: 'AI BOM', 
          href: '/ai-bom', 
          icon: <FileText size={20} />,
          badge: 'New',
          badgeColor: 'success',
          description: 'Bill of Materials'
        },
      ]
    },
    {
      id: 'operations',
      title: 'Operations',
      items: [
        { 
          id: 'model-upload',
          name: 'Upload Model', 
          href: '/model-upload', 
          icon: <Upload size={20} />,
          description: 'Register new models'
        },
        { 
          id: 'model-testing',
          name: 'Model Testing', 
          href: '/model-testing', 
          icon: <TestTube size={20} />,
          description: 'Test and validate'
        },
        { 
          id: 'monitoring',
          name: 'Monitoring', 
          href: '/monitoring', 
          icon: <Activity size={20} />,
          description: 'Real-time monitoring'
        },
        { 
          id: 'alerts',
          name: 'Alerts', 
          href: '/alerts', 
          icon: <AlertTriangle size={20} />,
          badge: '5',
          badgeColor: 'error',
          description: 'System alerts'
        },
      ]
    },
    {
      id: 'administration',
      title: 'Administration',
      items: [
        { 
          id: 'team',
          name: 'Team', 
          href: '/team', 
          icon: <Users size={20} />,
          description: 'User management'
        },
        { 
          id: 'settings',
          name: 'Settings', 
          href: '/settings', 
          icon: <Settings size={20} />,
          description: 'System configuration'
        },
        { 
          id: 'integrations',
          name: 'Integrations', 
          href: '/integrations', 
          icon: <Globe size={20} />,
          description: 'Third-party connections'
        },
      ]
    }
  ];

  const getPageTitle = () => {
    for (const section of navigationSections) {
      const item = section.items.find(item => item.href === pathname);
      if (item) return item.name;
    }
    return 'Dashboard';
  };

  const getPageDescription = () => {
    for (const section of navigationSections) {
      const item = section.items.find(item => item.href === pathname);
      if (item) return item.description;
    }
    return 'AI Governance Dashboard';
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => 
      prev.includes(sectionId) 
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const getBadgeColor = (color?: string) => {
    switch (color) {
      case 'success': return 'var(--spectrum-semantic-positive-color)';
      case 'warning': return 'var(--spectrum-semantic-warning-color)';
      case 'error': return 'var(--spectrum-semantic-notice-color)';
      default: return 'var(--spectrum-semantic-informative-color)';
    }
  };

  return (
    <div className="spectrum-layout">
      {/* Sidebar */}
      <aside 
        className={`spectrum-sidebar ${sidebarCollapsed ? 'collapsed' : ''} ${sidebarOpen ? 'open' : ''}`}
        style={{
          backgroundColor: 'var(--spectrum-semantic-background-color-default)',
          borderRight: '1px solid var(--spectrum-semantic-border-color-default)',
        }}
      >
        {/* Logo Section */}
        <div style={{
          padding: 'var(--spectrum-space-300) var(--spectrum-space-300) var(--spectrum-space-200)',
          borderBottom: '1px solid var(--spectrum-semantic-border-color-default)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: sidebarCollapsed ? 'center' : 'space-between',
          minHeight: '64px',
        }}>
          {!sidebarCollapsed && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spectrum-space-100)',
            }}>
              <div style={{
                width: '32px',
                height: '32px',
                backgroundColor: 'var(--spectrum-semantic-informative-color)',
                borderRadius: 'var(--spectrum-border-radius-100)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--spectrum-semantic-background-color-default)',
                fontWeight: 'var(--spectrum-font-weight-bold)',
                fontSize: 'var(--spectrum-font-size-200)',
              }}>
                F
              </div>
              <div>
                <div style={{
                  fontSize: 'var(--spectrum-font-size-300)',
                  fontWeight: 'var(--spectrum-font-weight-semibold)',
                  color: 'var(--spectrum-semantic-text-color-primary)',
                  lineHeight: 'var(--spectrum-line-height-tight)',
                }}>
                  FairMind
                </div>
                <div style={{
                  fontSize: 'var(--spectrum-font-size-75)',
                  color: 'var(--spectrum-semantic-text-color-tertiary)',
                  lineHeight: 'var(--spectrum-line-height-tight)',
                }}>
                  Ethical Sandbox
                </div>
              </div>
            </div>
          )}
          
          {sidebarCollapsed && (
            <div style={{
              width: '32px',
              height: '32px',
              backgroundColor: 'var(--spectrum-semantic-informative-color)',
              borderRadius: 'var(--spectrum-border-radius-100)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--spectrum-semantic-background-color-default)',
              fontWeight: 'var(--spectrum-font-weight-bold)',
              fontSize: 'var(--spectrum-font-size-200)',
            }}>
              F
            </div>
          )}

          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              border: 'none',
              backgroundColor: 'transparent',
              color: 'var(--spectrum-semantic-text-color-secondary)',
              cursor: 'pointer',
              borderRadius: 'var(--spectrum-border-radius-100)',
              transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
              e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
            }}
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronRight size={16} style={{ transform: 'rotate(180deg)' }} />}
          </button>
        </div>

        {/* Navigation */}
        <nav style={{
          flex: 1,
          padding: 'var(--spectrum-space-200) var(--spectrum-space-100)',
          overflowY: 'auto',
        }}>
          {navigationSections.map((section) => (
            <div key={section.id} style={{ marginBottom: 'var(--spectrum-space-300)' }}>
              {!sidebarCollapsed && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: 'var(--spectrum-space-100) var(--spectrum-space-200)',
                  marginBottom: 'var(--spectrum-space-100)',
                }}>
                  <button
                    onClick={() => toggleSection(section.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--spectrum-space-100)',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: 'var(--spectrum-semantic-text-color-secondary)',
                      cursor: 'pointer',
                      fontSize: 'var(--spectrum-font-size-100)',
                      fontWeight: 'var(--spectrum-font-weight-medium)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      transition: 'color var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                    }}
                  >
                    {expandedSections.includes(section.id) ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    {section.title}
                  </button>
                </div>
              )}

              {expandedSections.includes(section.id) && (
                <ul style={{
                  listStyle: 'none',
                  margin: 0,
                  padding: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--spectrum-space-50)',
                }}>
                  {section.items.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                      <li key={item.id}>
                        <a
                          href={item.href}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: sidebarCollapsed ? '0' : 'var(--spectrum-space-150)',
                            padding: sidebarCollapsed 
                              ? 'var(--spectrum-space-150)' 
                              : 'var(--spectrum-space-150) var(--spectrum-space-200)',
                            borderRadius: 'var(--spectrum-border-radius-100)',
                            textDecoration: 'none',
                            color: isActive 
                              ? 'var(--spectrum-semantic-informative-color)' 
                              : 'var(--spectrum-semantic-text-color-secondary)',
                            backgroundColor: isActive 
                              ? 'var(--spectrum-semantic-background-color-secondary)' 
                              : 'transparent',
                            fontWeight: isActive 
                              ? 'var(--spectrum-font-weight-medium)' 
                              : 'var(--spectrum-font-weight-regular)',
                            transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                            position: 'relative',
                            justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                          }}
                          onMouseEnter={(e) => {
                            if (!isActive) {
                              e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                              e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (!isActive) {
                              e.currentTarget.style.backgroundColor = 'transparent';
                              e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                            }
                          }}
                          title={sidebarCollapsed ? item.name : undefined}
                        >
                          <span style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '20px',
                            height: '20px',
                            flexShrink: 0,
                          }}>
                            {item.icon}
                          </span>
                          
                          {!sidebarCollapsed && (
                            <>
                              <span style={{
                                fontSize: 'var(--spectrum-font-size-200)',
                                lineHeight: 'var(--spectrum-line-height-tight)',
                                flex: 1,
                              }}>
                                {item.name}
                              </span>
                              
                              {item.badge && (
                                <span style={{
                                  padding: 'var(--spectrum-space-25) var(--spectrum-space-50)',
                                  backgroundColor: getBadgeColor(item.badgeColor),
                                  color: 'var(--spectrum-semantic-background-color-default)',
                                  borderRadius: 'var(--spectrum-border-radius-1000)',
                                  fontSize: 'var(--spectrum-font-size-50)',
                                  fontWeight: 'var(--spectrum-font-weight-medium)',
                                  lineHeight: 'var(--spectrum-line-height-tight)',
                                  minWidth: '16px',
                                  textAlign: 'center',
                                }}>
                                  {item.badge}
                                </span>
                              )}
                            </>
                          )}
                        </a>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          ))}
        </nav>

        {/* User Section */}
        {!sidebarCollapsed && (
          <div style={{
            padding: 'var(--spectrum-space-200)',
            borderTop: '1px solid var(--spectrum-semantic-border-color-default)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spectrum-space-150)',
              padding: 'var(--spectrum-space-150)',
              borderRadius: 'var(--spectrum-border-radius-100)',
              backgroundColor: 'var(--spectrum-semantic-background-color-secondary)',
            }}>
              <div style={{
                width: '32px',
                height: '32px',
                backgroundColor: 'var(--spectrum-semantic-informative-color)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--spectrum-semantic-background-color-default)',
                fontWeight: 'var(--spectrum-font-weight-medium)',
                fontSize: 'var(--spectrum-font-size-200)',
              }}>
                A
              </div>
              <div style={{ flex: 1 }}>
                <div style={{
                  fontSize: 'var(--spectrum-font-size-200)',
                  fontWeight: 'var(--spectrum-font-weight-medium)',
                  color: 'var(--spectrum-semantic-text-color-primary)',
                  lineHeight: 'var(--spectrum-line-height-tight)',
                }}>
                  Admin User
                </div>
                <div style={{
                  fontSize: 'var(--spectrum-font-size-100)',
                  color: 'var(--spectrum-semantic-text-color-secondary)',
                  lineHeight: 'var(--spectrum-line-height-tight)',
                }}>
                  admin@fairmind.ai
                </div>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 'var(--spectrum-z-index-modal-backdrop)',
          }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className={`spectrum-main ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        {/* Top Header */}
        <header className="spectrum-header">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
            gap: 'var(--spectrum-space-300)',
          }}>
            {/* Left Section */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spectrum-space-200)',
            }}>
              <button
                onClick={() => setSidebarOpen(true)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '40px',
                  height: '40px',
                  border: 'none',
                  backgroundColor: 'transparent',
                  color: 'var(--spectrum-semantic-text-color-secondary)',
                  cursor: 'pointer',
                  borderRadius: 'var(--spectrum-border-radius-100)',
                  transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                  e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                }}
              >
                <Menu size={20} />
              </button>
              
              <div>
                <h1 style={{
                  fontSize: 'var(--spectrum-font-size-400)',
                  fontWeight: 'var(--spectrum-font-weight-semibold)',
                  color: 'var(--spectrum-semantic-text-color-primary)',
                  margin: 0,
                  lineHeight: 'var(--spectrum-line-height-tight)',
                }}>
                  {getPageTitle()}
                </h1>
                <p style={{
                  fontSize: 'var(--spectrum-font-size-100)',
                  color: 'var(--spectrum-semantic-text-color-secondary)',
                  margin: 0,
                  lineHeight: 'var(--spectrum-line-height-normal)',
                }}>
                  {getPageDescription()}
                </p>
              </div>
            </div>

            {/* Right Section */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spectrum-space-200)',
            }}>
              {/* Search */}
              <div style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
              }}>
                <Search 
                  size={16} 
                  style={{
                    position: 'absolute',
                    left: 'var(--spectrum-space-150)',
                    color: 'var(--spectrum-semantic-text-color-tertiary)',
                  }}
                />
                <input
                  type="text"
                  placeholder="Search..."
                  style={{
                    padding: 'var(--spectrum-space-100) var(--spectrum-space-100) var(--spectrum-space-100) var(--spectrum-space-400)',
                    border: '1px solid var(--spectrum-semantic-border-color-default)',
                    borderRadius: 'var(--spectrum-border-radius-100)',
                    backgroundColor: 'var(--spectrum-semantic-background-color-default)',
                    color: 'var(--spectrum-semantic-text-color-primary)',
                    fontSize: 'var(--spectrum-font-size-200)',
                    width: '240px',
                    transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'var(--spectrum-semantic-border-color-focus)';
                    e.target.style.boxShadow = '0 0 0 2px rgba(38, 128, 235, 0.2)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'var(--spectrum-semantic-border-color-default)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>

              {/* Quick Actions */}
              <div style={{
                display: 'flex',
                gap: 'var(--spectrum-space-100)',
              }}>
                <button
                  style={{
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px',
                    border: 'none',
                    backgroundColor: 'transparent',
                    color: 'var(--spectrum-semantic-text-color-secondary)',
                    cursor: 'pointer',
                    borderRadius: 'var(--spectrum-border-radius-100)',
                    transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                    e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                  }}
                >
                  <Plus size={20} />
                </button>

                <button
                  style={{
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px',
                    border: 'none',
                    backgroundColor: 'transparent',
                    color: 'var(--spectrum-semantic-text-color-secondary)',
                    cursor: 'pointer',
                    borderRadius: 'var(--spectrum-border-radius-100)',
                    transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                    e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                  }}
                >
                  <Bell size={20} />
                  <span style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    width: '8px',
                    height: '8px',
                    backgroundColor: 'var(--spectrum-semantic-notice-color)',
                    borderRadius: '50%',
                  }} />
                </button>

                <button
                  style={{
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px',
                    border: 'none',
                    backgroundColor: 'transparent',
                    color: 'var(--spectrum-semantic-text-color-secondary)',
                    cursor: 'pointer',
                    borderRadius: 'var(--spectrum-border-radius-100)',
                    transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                    e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                  }}
                >
                  <HelpCircle size={20} />
                </button>
              </div>

              {/* User Menu */}
              <div style={{ position: 'relative' }}>
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--spectrum-space-100)',
                    padding: 'var(--spectrum-space-100) var(--spectrum-space-150)',
                    border: '1px solid var(--spectrum-semantic-border-color-default)',
                    borderRadius: 'var(--spectrum-border-radius-100)',
                    backgroundColor: 'var(--spectrum-semantic-background-color-default)',
                    color: 'var(--spectrum-semantic-text-color-primary)',
                    cursor: 'pointer',
                    fontSize: 'var(--spectrum-font-size-200)',
                    transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-default)';
                  }}
                >
                  <div style={{
                    width: '32px',
                    height: '32px',
                    backgroundColor: 'var(--spectrum-semantic-informative-color)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--spectrum-semantic-background-color-default)',
                    fontWeight: 'var(--spectrum-font-weight-medium)',
                    fontSize: 'var(--spectrum-font-size-200)',
                  }}>
                    A
                  </div>
                  <span>Admin</span>
                  <ChevronDown size={16} />
                </button>

                {userMenuOpen && (
                  <div style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: 'var(--spectrum-space-50)',
                    backgroundColor: 'var(--spectrum-semantic-background-color-default)',
                    border: '1px solid var(--spectrum-semantic-border-color-default)',
                    borderRadius: 'var(--spectrum-border-radius-200)',
                    boxShadow: 'var(--spectrum-shadow-300)',
                    minWidth: '200px',
                    zIndex: 'var(--spectrum-z-index-dropdown)',
                  }}>
                    <div style={{
                      padding: 'var(--spectrum-space-200)',
                      borderBottom: '1px solid var(--spectrum-semantic-border-color-default)',
                    }}>
                      <div style={{
                        fontSize: 'var(--spectrum-font-size-200)',
                        fontWeight: 'var(--spectrum-font-weight-medium)',
                        color: 'var(--spectrum-semantic-text-color-primary)',
                      }}>
                        Admin User
                      </div>
                      <div style={{
                        fontSize: 'var(--spectrum-font-size-100)',
                        color: 'var(--spectrum-semantic-text-color-secondary)',
                      }}>
                        admin@fairmind.ai
                      </div>
                    </div>
                    
                    <div style={{
                      padding: 'var(--spectrum-space-100)',
                    }}>
                      <a
                        href="#profile"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--spectrum-space-150)',
                          padding: 'var(--spectrum-space-100) var(--spectrum-space-150)',
                          color: 'var(--spectrum-semantic-text-color-secondary)',
                          textDecoration: 'none',
                          borderRadius: 'var(--spectrum-border-radius-100)',
                          fontSize: 'var(--spectrum-font-size-200)',
                          transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                          e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                          e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                        }}
                      >
                        <User size={16} />
                        Profile
                      </a>
                      <a
                        href="#help"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--spectrum-space-150)',
                          padding: 'var(--spectrum-space-100) var(--spectrum-space-150)',
                          color: 'var(--spectrum-semantic-text-color-secondary)',
                          textDecoration: 'none',
                          borderRadius: 'var(--spectrum-border-radius-100)',
                          fontSize: 'var(--spectrum-font-size-200)',
                          transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                          e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-primary)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                          e.currentTarget.style.color = 'var(--spectrum-semantic-text-color-secondary)';
                        }}
                      >
                        <HelpCircle size={16} />
                        Help
                      </a>
                      <a
                        href="#logout"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--spectrum-space-150)',
                          padding: 'var(--spectrum-space-100) var(--spectrum-space-150)',
                          color: 'var(--spectrum-semantic-notice-color)',
                          textDecoration: 'none',
                          borderRadius: 'var(--spectrum-border-radius-100)',
                          fontSize: 'var(--spectrum-font-size-200)',
                          transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--spectrum-semantic-background-color-secondary)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <LogOut size={16} />
                        Sign Out
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="spectrum-content">
          {children}
        </main>
      </div>
    </div>
  );
}; 
