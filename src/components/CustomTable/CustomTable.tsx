import Box from '@mui/material/Box'
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
import { useState } from 'react'

const rows = [
  { id: 1, name: 'Alice', age: 25, department: 'Development' },
  { id: 2, name: 'Bob', age: 30, department: 'Finance' },
  { id: 3, name: 'Charlie', age: 35, department: 'Marketing' },
  { id: 4, name: 'David', age: 28, department: 'HR' },
  { id: 5, name: 'Eve', age: 40, department: 'Operations' },
  { id: 6, name: 'Frank', age: 32, department: 'IT' },
  { id: 7, name: 'Grace', age: 27, department: 'Sales' },
  { id: 8, name: 'Hank', age: 34, department: 'Logistics' },
  { id: 9, name: 'Eve', age: 40, department: 'Operations' },
  { id: 10, name: 'Frank', age: 32, department: 'IT' },
  { id: 11, name: 'Grace', age: 27, department: 'Sales' },
  { id: 12, name: 'Hank', age: 34, department: 'Logistics' }
]

export const CustomTable = () => {
  const [selected, setSelected] = useState<number[]>([])
  const [page, setPage] = useState(0)
  const rowsPerPage = 12

  const isAllSelected = selected.length === rows.length
  const isIndeterminate = selected.length > 0 && selected.length < rows.length

  const paginatedRows = rows.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  )

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelected(rows.map((row) => row.id))
    } else {
      setSelected([])
    }
  }

  const handleSelectRow =
    (id: number) => (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.target.checked) {
        setSelected((prevSelected) => [...prevSelected, id])
      } else {
        setSelected((prevSelected) =>
          prevSelected.filter((selectedId) => selectedId !== id)
        )
      }
    }

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage)
  }

  return (
    <Box sx={{ width: '100%' }}>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={isIndeterminate}
                  checked={isAllSelected}
                  onChange={handleSelectAll} // 全選事件處理
                />
              </TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Age</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedRows.map((row) => (
              <TableRow
                key={row.id}
                hover
                selected={selected.includes(row.id)} // 高亮選中行
              >
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.includes(row.id)} // 單行選中狀態
                    onChange={handleSelectRow(row.id)} // 單行選中事件處理
                  />
                </TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell>{row.age}</TableCell>
                <TableCell>{row.department}</TableCell>
                <TableCell>
                  <IconButton aria-label="edit">
                    <EditIcon />
                  </IconButton>
                  <IconButton aria-label="delete">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={rows.length}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage} // 固定每頁顯示的資料數
        rowsPerPageOptions={[]} // 移除下拉選單
      />
    </Box>
  )
}
