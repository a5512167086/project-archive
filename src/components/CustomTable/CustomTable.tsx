import React, { SetStateAction, useState } from 'react'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Paper from '@mui/material/Paper'
import Checkbox from '@mui/material/Checkbox'
import IconButton from '@mui/material/IconButton'
import TablePagination from '@mui/material/TablePagination'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import { useTranslation } from 'react-i18next'

interface TableColumn {
  id: string
  label: string
  align?: 'left' | 'right' | 'center'
}

interface CustomTableProps<T> {
  data: T[]
  columns: TableColumn[]
  onEdit?: (item: T) => void
  onDelete?: (item: T) => void
  rowsPerPage?: number
  selected: number[]
  setSelected: React.Dispatch<SetStateAction<number[]>>
}

export const CustomTable = <T,>({
  data,
  columns,
  onEdit,
  onDelete,
  rowsPerPage = 10,
  selected,
  setSelected
}: CustomTableProps<T>) => {
  const [page, setPage] = useState(0)
  const { t } = useTranslation()
  const currentPageIndexes = data
    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
    .map((_, index) => page * rowsPerPage + index)

  const isAllSelected = currentPageIndexes.every((index) =>
    selected.includes(index)
  )
  const isIndeterminate =
    currentPageIndexes.some((index) => selected.includes(index)) &&
    !isAllSelected

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelected((prevSelected) => [
        ...new Set([...prevSelected, ...currentPageIndexes])
      ])
    } else {
      setSelected((prevSelected) =>
        prevSelected.filter((index) => !currentPageIndexes.includes(index))
      )
    }
  }

  const handleSelectRow =
    (rowIndex: number) => (event: React.ChangeEvent<HTMLInputElement>) => {
      setSelected((prevSelected) =>
        event.target.checked
          ? [...prevSelected, rowIndex]
          : prevSelected.filter((index) => index !== rowIndex)
      )
    }

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage)
  }

  return (
    <Paper sx={{ width: '100%' }}>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={isIndeterminate}
                  checked={isAllSelected}
                  onChange={handleSelectAll}
                />
              </TableCell>
              {columns.map((column) => (
                <TableCell key={column.id} align={column.align || 'left'}>
                  {t(column.label)}
                </TableCell>
              ))}
              <TableCell>{t('common.action')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row, index) => {
                const globalIndex = page * rowsPerPage + index
                return (
                  <TableRow
                    key={globalIndex}
                    hover
                    selected={selected.includes(globalIndex)}
                  >
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selected.includes(globalIndex)}
                        onChange={handleSelectRow(globalIndex)}
                      />
                    </TableCell>
                    {columns.map((column) => (
                      <TableCell
                        key={column.id}
                        align={column.align || 'left'}
                        sx={{
                          maxWidth: 150,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                      >
                        {String(row[column.id as keyof T] ?? '')}
                      </TableCell>
                    ))}
                    <TableCell>
                      {onEdit && (
                        <IconButton onClick={() => onEdit(row)}>
                          <EditIcon />
                        </IconButton>
                      )}
                      {onDelete && (
                        <IconButton onClick={() => onDelete(row)}>
                          <DeleteIcon />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={data.length}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        rowsPerPageOptions={[]}
      />
    </Paper>
  )
}
