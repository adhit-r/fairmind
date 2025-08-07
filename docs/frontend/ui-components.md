# UI Components & Design System

## 🎨 Design System Overview

Fairmind v2 follows a modern, accessible design system built on **Tailwind CSS** and **Radix UI** primitives, ensuring consistency, performance, and excellent user experience across all interfaces.

### Design Principles

- **Accessibility First**: WCAG 2.1 AA compliance
- **Performance Optimized**: Minimal bundle size, efficient rendering
- **Consistency**: Unified visual language and interaction patterns
- **Scalability**: Modular components that scale with the platform
- **Data-Driven**: Components designed for complex data visualization

## 🏗️ Component Architecture

### Component Library Structure

```
packages/ui/
├── components/
│   ├── primitives/          # Base Radix UI components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── composite/           # Complex composed components
│   │   ├── data-table.tsx
│   │   ├── command-palette.tsx
│   │   └── ...
│   ├── charts/              # Specialized chart components
│   │   ├── bias-chart.tsx
│   │   ├── compliance-radar.tsx
│   │   └── ...
│   └── layouts/             # Layout components
│       ├── dashboard-layout.tsx
│       ├── sidebar-layout.tsx
│       └── ...
├── styles/
│   ├── globals.css          # Global styles
│   └── components.css       # Component-specific styles
├── lib/
│   ├── utils.ts            # Utility functions
│   └── constants.ts        # Design tokens
└── index.ts                # Main export file
```

## 🎯 Core UI Components

### Button Component System

```typescript
// packages/ui/components/button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        success: "bg-green-600 text-white hover:bg-green-700",
        warning: "bg-yellow-600 text-white hover:bg-yellow-700"
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        xl: "h-12 rounded-lg px-10 text-base",
        icon: "h-10 w-10"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
  loadingText?: string
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading, loadingText, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {loading ? loadingText || "Loading..." : children}
      </Comp>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

### Enhanced Data Table Component

```typescript
// packages/ui/components/data-table.tsx
"use client"

import * as React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown, MoreHorizontal, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  searchKey?: string
  searchPlaceholder?: string
  onRowClick?: (row: TData) => void
  enableSelection?: boolean
  enablePagination?: boolean
  pageSize?: number
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchKey,
  searchPlaceholder = "Search...",
  onRowClick,
  enableSelection = false,
  enablePagination = true,
  pageSize = 10
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})

  // Add selection column if enabled
  const enhancedColumns = React.useMemo(() => {
    if (!enableSelection) return columns

    const selectionColumn: ColumnDef<TData, TValue> = {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
        />
      ),
      enableSorting: false,
      enableHiding: false,
    }

    return [selectionColumn, ...columns]
  }, [columns, enableSelection])

  const table = useReactTable({
    data,
    columns: enhancedColumns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: enablePagination ? getPaginationRowModel() : undefined,
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
  })

  return (
    <div className="w-full">
      <div className="flex items-center justify-between py-4">
        {searchKey && (
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={searchPlaceholder}
              value={(table.getColumn(searchKey)?.getFilterValue() as string) ?? ""}
              onChange={(event) =>
                table.getColumn(searchKey)?.setFilterValue(event.target.value)
              }
              className="pl-10"
            />
          </div>
        )}
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="ml-auto">
              Columns <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => {
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    className="capitalize"
                    checked={column.getIsVisible()}
                    onCheckedChange={(value) =>
                      column.toggleVisibility(!!value)
                    }
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                )
              })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className={onRowClick ? "cursor-pointer hover:bg-muted/50" : ""}
                  onClick={() => onRowClick?.(row.original)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={enhancedColumns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      
      {enablePagination && (
        <div className="flex items-center justify-end space-x-2 py-4">
          <div className="flex-1 text-sm text-muted-foreground">
            {enableSelection && (
              <>
                {table.getFilteredSelectedRowModel().rows.length} of{" "}
                {table.getFilteredRowModel().rows.length} row(s) selected.
              </>
            )}
          </div>
          <div className="space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Previous
            </Button>
            <Button
              variant="outline"  
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to create sortable column header
export function createSortableHeader<T>(title: string, accessorKey: keyof T) {
  return ({ column }: { column: any }) => {
    return (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="h-auto p-0 font-semibold"
      >
        {title}
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    )
  }
}

// Status badge component for tables
export function StatusBadge({ status }: { status: string }) {
  const statusConfig = {
    completed: { variant: "default" as const, label: "Completed" },
    running: { variant: "secondary" as const, label: "Running" },
    failed: { variant: "destructive" as const, label: "Failed" },
    queued: { variant: "outline" as const, label: "Queued" },
    cancelled: { variant: "outline" as const, label: "Cancelled" }
  }

  const config = statusConfig[status as keyof typeof statusConfig] || {
    variant: "secondary" as const,
    label: status
  }

  return <Badge variant={config.variant}>{config.label}</Badge>
}
```

## 📊 Specialized Chart Components

### Bias Visualization Chart

```typescript
// packages/ui/components/charts/bias-chart.tsx
"use client"

import * as React from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
  ReferenceLine
} from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react"

interface BiasMetric {
  group: string
  value: number
  threshold: number
  status: "pass" | "warning" | "fail"
  sampleSize: number
  confidenceInterval?: {
    lower: number
    upper: number
  }
}

interface BiasChartProps {
  data: BiasMetric[]
  title: string
  description?: string
  type: "demographic_parity" | "equalized_odds" | "individual_fairness"
  interactive?: boolean
  onGroupSelect?: (group: string) => void
  className?: string
}

const STATUS_COLORS = {
  pass: "#10b981", // green-500
  warning: "#f59e0b", // amber-500
  fail: "#ef4444" // red-500
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as BiasMetric
    
    return (
      <div className="rounded-lg border bg-background p-3 shadow-md">
        <div className="grid gap-2">
          <div className="flex items-center gap-2">
            <div className="font-semibold">{label}</div>
            <StatusIcon status={data.status} />
          </div>
          <div className="grid gap-1 text-sm">
            <div>Value: {(data.value * 100).toFixed(2)}%</div>
            <div>Threshold: {(data.threshold * 100).toFixed(2)}%</div>
            <div>Sample Size: {data.sampleSize.toLocaleString()}</div>
            {data.confidenceInterval && (
              <div>
                95% CI: [{(data.confidenceInterval.lower * 100).toFixed(2)}%, {(data.confidenceInterval.upper * 100).toFixed(2)}%]
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }
  return null
}

const StatusIcon = ({ status }: { status: "pass" | "warning" | "fail" }) => {
  switch (status) {
    case "pass":
      return <CheckCircle className="h-4 w-4 text-green-500" />
    case "warning":
      return <AlertTriangle className="h-4 w-4 text-amber-500" />
    case "fail":
      return <XCircle className="h-4 w-4 text-red-500" />
  }
}

export function BiasChart({
  data,
  title,
  description,
  type,
  interactive = false,
  onGroupSelect,
  className
}: BiasChartProps) {
  const [selectedGroup, setSelectedGroup] = React.useState<string | null>(null)

  const handleBarClick = (data: BiasMetric) => {
    if (interactive) {
      setSelectedGroup(data.group)
      onGroupSelect?.(data.group)
    }
  }

  const overallStatus = React.useMemo(() => {
    const failCount = data.filter(d => d.status === "fail").length
    const warningCount = data.filter(d => d.status === "warning").length
    
    if (failCount > 0) return "fail"
    if (warningCount > 0) return "warning"
    return "pass"
  }, [data])

  // Calculate average threshold for reference line
  const avgThreshold = data.reduce((sum, d) => sum + d.threshold, 0) / data.length

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {title}
              <StatusIcon status={overallStatus} />
            </CardTitle>
            {description && (
              <CardDescription>{description}</CardDescription>
            )}
          </div>
          <div className="flex gap-2">
            <Badge variant={overallStatus === "pass" ? "default" : overallStatus === "warning" ? "secondary" : "destructive"}>
              {overallStatus.toUpperCase()}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="group" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine 
                y={avgThreshold} 
                stroke="#6b7280" 
                strokeDasharray="5 5"
                label={{ 
                  value: "Threshold", 
                  position: "topRight", 
                  fontSize: 12 
                }}
              />
              <Bar 
                dataKey="value" 
                radius={[4, 4, 0, 0]}
                cursor={interactive ? "pointer" : "default"}
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={STATUS_COLORS[entry.status]}
                    onClick={() => handleBarClick(entry)}
                    stroke={selectedGroup === entry.group ? "#1f2937" : "none"}
                    strokeWidth={selectedGroup === entry.group ? 2 : 0}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Legend */}
        <div className="mt-4 flex items-center justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded bg-green-500" />
            <span>Pass</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded bg-amber-500" />
            <span>Warning</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded bg-red-500" />
            <span>Fail</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Compliance Radar Chart

```typescript
// packages/ui/components/charts/compliance-radar.tsx
"use client"

import * as React from "react"
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip
} from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface ComplianceData {
  category: string
  score: number
  maxScore: number
  benchmark?: number
  description: string
}

interface ComplianceRadarProps {
  data: ComplianceData[]
  title: string
  description?: string
  overallScore: number
  className?: string
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as ComplianceData
    
    return (
      <div className="rounded-lg border bg-background p-3 shadow-md">
        <div className="grid gap-2">
          <div className="font-semibold">{label}</div>
          <div className="grid gap-1 text-sm">
            <div>Score: {data.score}/{data.maxScore}</div>
            <div>Percentage: {Math.round((data.score / data.maxScore) * 100)}%</div>
            {data.benchmark && (
              <div>Benchmark: {Math.round((data.benchmark / data.maxScore) * 100)}%</div>
            )}
            <div className="text-muted-foreground">{data.description}</div>
          </div>
        </div>
      </div>
    )
  }
  return null
}

export function ComplianceRadar({
  data,
  title,
  description,
  overallScore,
  className
}: ComplianceRadarProps) {
  // Convert data to percentage for radar chart
  const radarData = data.map(item => ({
    ...item,
    percentage: Math.round((item.score / item.maxScore) * 100),
    benchmarkPercentage: item.benchmark ? Math.round((item.benchmark / item.maxScore) * 100) : undefined
  }))

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600"
    if (score >= 70) return "text-amber-600"
    return "text-red-600"
  }

  const getScoreBadge = (score: number) => {
    if (score >= 90) return { variant: "default" as const, label: "Excellent" }
    if (score >= 70) return { variant: "secondary" as const, label: "Good" }
    if (score >= 50) return { variant: "outline" as const, label: "Fair" }
    return { variant: "destructive" as const, label: "Poor" }
  }

  const scoreBadge = getScoreBadge(overallScore)

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            {description && (
              <CardDescription>{description}</CardDescription>
            )}
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${getScoreColor(overallScore)}`}>
              {overallScore}%
            </div>
            <Badge variant={scoreBadge.variant} className="mt-1">
              {scoreBadge.label}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid gridType="polygon" />
              <PolarAngleAxis 
                dataKey="category" 
                tick={{ fontSize: 12 }}
                className="text-sm"
              />
              <PolarRadiusAxis 
                angle={90} 
                domain={[0, 100]}
                tick={{ fontSize: 10 }}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              
              {/* Current scores */}
              <Radar
                name="Current Score"
                dataKey="percentage"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              
              {/* Benchmark scores (if available) */}
              {radarData.some(d => d.benchmarkPercentage) && (
                <Radar
                  name="Industry Benchmark"
                  dataKey="benchmarkPercentage"
                  stroke="#6b7280"
                  fill="transparent"
                  strokeWidth={1}
                  strokeDasharray="5,5"
                />
              )}
              
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Score breakdown */}
        <div className="mt-4 grid gap-2">
          <h4 className="text-sm font-semibold">Category Breakdown</h4>
          <div className="grid gap-1">
            {data.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span>{item.category}</span>
                <span className={getScoreColor((item.score / item.maxScore) * 100)}>
                  {item.score}/{item.maxScore} ({Math.round((item.score / item.maxScore) * 100)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

## 🎨 Design Tokens & Theme System

### Tailwind Configuration

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
    '../../packages/ui/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Fairmind-specific colors
        bias: {
          pass: "#10b981",
          warning: "#f59e0b", 
          fail: "#ef4444"
        },
        compliance: {
          excellent: "#059669",
          good: "#0891b2",
          fair: "#ea580c",
          poor: "#dc2626"
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
        "fade-in": {
          "0%": { opacity: 0, transform: "translateY(10px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 5px rgba(59, 130, 246, 0.5)" },
          "50%": { boxShadow: "0 0 20px rgba(59, 130, 246, 0.8)" },
        }
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      }
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### CSS Variables for Theme

```css
/* packages/ui/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 84% 4.9%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 94.1%;
  }
}

@layer components {
  /* Custom component styles */
  .bias-chart-container {
    @apply rounded-lg border border-border bg-card p-4;
  }
  
  .compliance-score-excellent {
    @apply text-green-600 dark:text-green-400;
  }
  
  .compliance-score-good {
    @apply text-blue-600 dark:text-blue-400;
  }
  
  .compliance-score-fair {
    @apply text-orange-600 dark:text-orange-400;
  }
  
  .compliance-score-poor {
    @apply text-red-600 dark:text-red-400;
  }
  
  .data-point-pass {
    @apply fill-green-500 stroke-green-600;
  }
  
  .data-point-warning {
    @apply fill-amber-500 stroke-amber-600;
  }
  
  .data-point-fail {
    @apply fill-red-500 stroke-red-600;
  }
}

@layer utilities {
  /* Custom utility classes */
  .text-balance {
    text-wrap: balance;
  }
  
  .animate-fade-in-up {
    animation: fade-in-up 0.3s ease-out;
  }
  
  @keyframes fade-in-up {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}
```

This comprehensive UI component system and design framework provides a solid foundation for building consistent, accessible, and performant user interfaces across the Fairmind v2 platform.
