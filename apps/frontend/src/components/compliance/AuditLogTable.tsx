'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ChevronUp, ChevronDown, Download, Search } from 'lucide-react';

interface AuditLogEntry {
  timestamp: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string;
}

interface AuditLogTableProps {
  data: AuditLogEntry[];
  isLoading?: boolean;
  actionFilter?: string;
}

type SortKey = keyof AuditLogEntry;
type SortOrder = 'asc' | 'desc';

export function AuditLogTable({
  data,
  isLoading = false,
  actionFilter
}: AuditLogTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('timestamp');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 25;

  // Filter and sort data
  const filteredData = useMemo(() => {
    let result = data;

    // Apply action filter
    if (actionFilter) {
      result = result.filter((entry) => entry.action === actionFilter);
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (entry) =>
          entry.user_email.toLowerCase().includes(query) ||
          entry.resource_id.toLowerCase().includes(query)
      );
    }

    // Sort
    result.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (typeof aVal === 'string') {
        return sortOrder === 'asc'
          ? (aVal as string).localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal as string);
      }

      return 0;
    });

    return result;
  }, [data, actionFilter, searchQuery, sortKey, sortOrder]);

  // Pagination
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const paginatedData = filteredData.slice(startIdx, startIdx + itemsPerPage);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
    setCurrentPage(1);
  };

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return <span className="text-gray-300">⋮</span>;
    return sortOrder === 'asc' ? (
      <ChevronUp className="inline h-4 w-4" />
    ) : (
      <ChevronDown className="inline h-4 w-4" />
    );
  };

  const exportCSV = () => {
    const headers = [
      'Timestamp',
      'User Email',
      'Action',
      'Resource Type',
      'Resource ID',
      'IP Address'
    ];
    const rows = paginatedData.map((entry) => [
      entry.timestamp,
      entry.user_email,
      entry.action,
      entry.resource_type,
      entry.resource_id,
      entry.ip_address
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Card className="border-4 border-black shadow-brutal">
      <CardHeader className="border-b-4 border-black">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold tracking-tight">AUDIT LOG</CardTitle>
          <Button
            onClick={exportCSV}
            disabled={paginatedData.length === 0}
            className="border-2 border-black bg-white text-black font-bold hover:bg-gray-100 shadow-brutal disabled:opacity-50"
          >
            <Download className="mr-2 h-4 w-4" />
            EXPORT CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        {/* Search Box */}
        <div className="mb-4 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by email or resource ID..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="border-2 border-black pl-10 focus:ring-2 focus:ring-orange-500"
          />
        </div>

        {/* Table */}
        <div className="overflow-x-auto border-2 border-black">
          <Table>
            <TableHeader className="bg-gray-50 border-b-2 border-black">
              <TableRow className="border-0">
                <TableHead
                  className="cursor-pointer font-bold text-xs uppercase border-r-2 border-black hover:bg-gray-100"
                  onClick={() => handleSort('timestamp')}
                >
                  TIMESTAMP <SortIcon column="timestamp" />
                </TableHead>
                <TableHead
                  className="cursor-pointer font-bold text-xs uppercase border-r-2 border-black hover:bg-gray-100"
                  onClick={() => handleSort('user_email')}
                >
                  USER <SortIcon column="user_email" />
                </TableHead>
                <TableHead
                  className="cursor-pointer font-bold text-xs uppercase border-r-2 border-black hover:bg-gray-100"
                  onClick={() => handleSort('action')}
                >
                  ACTION <SortIcon column="action" />
                </TableHead>
                <TableHead className="cursor-pointer font-bold text-xs uppercase border-r-2 border-black hover:bg-gray-100">
                  RESOURCE TYPE
                </TableHead>
                <TableHead className="cursor-pointer font-bold text-xs uppercase border-r-2 border-black hover:bg-gray-100">
                  RESOURCE ID
                </TableHead>
                <TableHead className="font-bold text-xs uppercase">IP ADDRESS</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : paginatedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    No audit logs found
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((entry, idx) => (
                  <TableRow
                    key={idx}
                    className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <TableCell className="font-mono text-xs border-r border-gray-200">
                      {new Date(entry.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-xs border-r border-gray-200">
                      {entry.user_email}
                    </TableCell>
                    <TableCell className="text-xs border-r border-gray-200 font-medium">
                      <span className="px-2 py-1 bg-orange-100 border border-orange-300 rounded">
                        {entry.action}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs border-r border-gray-200">
                      {entry.resource_type}
                    </TableCell>
                    <TableCell className="text-xs border-r border-gray-200 font-mono">
                      {entry.resource_id}
                    </TableCell>
                    <TableCell className="text-xs font-mono">{entry.ip_address}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <p className="text-xs text-gray-600">
              Showing {startIdx + 1} to {Math.min(startIdx + itemsPerPage, filteredData.length)} of{' '}
              {filteredData.length} results
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                variant="outline"
                className="border-2 border-black font-bold disabled:opacity-50"
              >
                ← PREV
              </Button>
              <Button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                variant="outline"
                className="border-2 border-black font-bold disabled:opacity-50"
              >
                NEXT →
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
