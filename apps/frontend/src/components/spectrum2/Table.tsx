import React from 'react';

interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
}

interface TableProps {
  columns: TableColumn[];
  data: any[];
  onSort?: (column: string) => void;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  className?: string;
  emptyMessage?: string;
}

export const Table: React.FC<TableProps> = ({
  columns,
  data,
  onSort,
  sortColumn,
  sortDirection,
  className = '',
  emptyMessage = 'No data available',
}) => {
  const handleSort = (column: TableColumn) => {
    if (column.sortable && onSort) {
      onSort(column.key);
    }
  };

  return (
    <div className={`spectrum-table-container ${className}`}>
      <table className="spectrum-table">
        <thead className="spectrum-table-head">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`spectrum-table-headCell ${
                  column.sortable ? 'spectrum-table-headCell--sortable' : ''
                }`}
                style={{ width: column.width }}
                onClick={() => handleSort(column)}
              >
                <div className="spectrum-table-headCellContent">
                  {column.label}
                  {column.sortable && sortColumn === column.key && (
                    <span className="spectrum-table-sortedIcon">
                      {sortDirection === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="spectrum-table-body">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="spectrum-table-cell spectrum-table-cell--empty"
              >
                <div className="spectrum-table-emptyMessage">
                  {emptyMessage}
                </div>
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr key={rowIndex} className="spectrum-table-row">
                {columns.map((column) => (
                  <td key={column.key} className="spectrum-table-cell">
                    {row[column.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
