import { useEffect, useMemo, useState } from 'react'
import {
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid2,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TableSortLabel,
  TablePagination,
  Toolbar,
  InputAdornment,
  SelectChangeEvent
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'
import {
  useLazyGetOrdersQuery,
  useUpdateOrderMutation,
  GetOrdersResponse,
  UpdateOrderRequest
} from '@/store/apis/orderApi'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { PAGE_PATHS } from '@/routes'
import { showSuccessToast } from '@/utils/toast'
import { StyledOrderManagementPage } from './OrderManagementPage.style'
import { useLazyGetProductsQuery } from '@/store/apis/productApi'
import { useParams } from 'react-router-dom'

const orderManagementPageContent = {
  title: 'orderManagementPage.title',
  botPageTitle: 'botPage.myBot'
}

type Order = 'asc' | 'desc'
type SortableColumn = 'recipient_name' | 'created_at'

function descendingComparator(
  a: GetOrdersResponse,
  b: GetOrdersResponse,
  orderBy: SortableColumn
) {
  if (b[orderBy] < a[orderBy]) {
    return -1
  }
  if (b[orderBy] > a[orderBy]) {
    return 1
  }
  return 0
}

function getComparator(
  order: Order,
  orderBy: SortableColumn
): (a: GetOrdersResponse, b: GetOrdersResponse) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy)
}

const OrderManagementPage = () => {
  const { t } = useTranslation()
  const { uuid } = useParams()
  const { botList } = useAppSelector((state) => state.bot)
  const { orders } = useAppSelector((state) => state.order)
  const { products } = useAppSelector((state) => state.product)
  const currentBot = botList.find((bot) => bot.bot_detail_id === uuid)
  // API hooks
  const [getOrders] = useLazyGetOrdersQuery()
  const [getProducts] = useLazyGetProductsQuery()
  const [updateOrder] = useUpdateOrderMutation()

  // Dialog state
  const [selectedOrder, setSelectedOrder] = useState<GetOrdersResponse | null>(
    null
  )
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editForm, setEditForm] = useState<Partial<UpdateOrderRequest>>({})

  // Table state
  const [order, setOrder] = useState<Order>('asc')
  const [orderBy, setOrderBy] = useState<SortableColumn>('created_at')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(5)
  const [filterName, setFilterName] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')

  // Fetch orders when component mounts or bot changes
  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getOrders({ bot_uuid: currentBot.bot_detail_id })
      getProducts({ bot_uuid: currentBot.bot_detail_id })
    }
  }, [currentBot, getOrders, getProducts])

  const handleRequestSort = (
    _: React.MouseEvent<unknown>,
    property: SortableColumn
  ) => {
    const isAsc = orderBy === property && order === 'asc'
    setOrder(isAsc ? 'desc' : 'asc')
    setOrderBy(property)
  }

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleFilterByName = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPage(0)
    setFilterName(event.target.value)
  }

  const handleStatusFilterChange = (event: SelectChangeEvent<string>) => {
    setPage(0)
    setStatusFilter(event.target.value)
  }

  const handleStartDateChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setPage(0)
    setStartDate(event.target.value)
  }

  const handleEndDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPage(0)
    setEndDate(event.target.value)
  }

  const handleResetFilters = () => {
    setFilterName('')
    setStatusFilter('all')
    setStartDate('')
    setEndDate('')
  }

  const filteredOrders = useMemo(() => {
    const lowercasedFilter = filterName.toLowerCase()
    return orders
      .filter(
        (order) =>
          order.recipient_name.toLowerCase().includes(lowercasedFilter) ||
          order.order_id.toLowerCase().includes(lowercasedFilter)
      )
      .filter((order) =>
        statusFilter === 'all' ? true : order.status === statusFilter
      )
      .filter((order) => {
        if (!startDate || !endDate) return true
        const orderDate = new Date(order.created_at)
        const start = new Date(startDate)
        const end = new Date(endDate)
        end.setHours(23, 59, 59, 999) // Set end date to end of day
        return orderDate >= start && orderDate <= end
      })
      .sort(getComparator(order, orderBy))
  }, [orders, order, orderBy, filterName, statusFilter, startDate, endDate])

  // Handle order click
  const handleOrderClick = (order: GetOrdersResponse) => {
    setSelectedOrder(order)
    setEditForm({
      bot_uuid: currentBot!.bot_detail_id,
      order_id: order.order_id,
      status: order.status,
      payment_status: order.payment_status,
      tracking_number: order.tracking_number
    })
    setDialogOpen(true)
  }

  // Handle form change
  const handleFormChange = <K extends keyof UpdateOrderRequest>(
    field: K,
    value: UpdateOrderRequest[K]
  ) => {
    setEditForm((prev) => ({ ...prev, [field]: value }))
  }

  // Handle form submit
  const handleSubmit = async () => {
    if (!editForm.bot_uuid || !editForm.order_id) return

    await updateOrder(editForm as UpdateOrderRequest).unwrap()
    showSuccessToast('success.data_updated', t)
    setDialogOpen(false)
    // Refresh orders
    if (currentBot?.bot_detail_id) {
      getOrders({ bot_uuid: currentBot.bot_detail_id })
    }
  }

  // Handle dialog close
  const handleDialogClose = () => {
    setDialogOpen(false)
    setSelectedOrder(null)
    setEditForm({})
  }

  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: t(orderManagementPageContent.botPageTitle)
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBot?.bot_detail_id}`,
      linkText: currentBot?.chinese_name ?? ''
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBot?.bot_detail_id}/${PAGE_PATHS.ORDER_MANAGEMENT}`,
      linkText: t(orderManagementPageContent.title)
    }
  ]

  return (
    <StyledOrderManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box>
        <Typography
          variant="h5"
          sx={{
            fontSize: '2rem',
            fontWeight: '500'
          }}
        >
          {t(orderManagementPageContent.title)}
        </Typography>
      </Box>

      <Paper
        sx={{
          width: '100%',
          mt: 2,
          display: 'flex',
          flex: 1,
          flexDirection: 'column'
        }}
      >
        <Toolbar sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
          <TextField
            variant="outlined"
            value={filterName}
            onChange={handleFilterByName}
            placeholder={t('orderManagementPage.searchPlaceholder')}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              )
            }}
            sx={{ flexGrow: 1, minWidth: '200px' }}
          />
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>{t('orderManagementPage.status')}</InputLabel>
            <Select
              value={statusFilter}
              label={t('orderManagementPage.status')}
              onChange={handleStatusFilterChange}
            >
              <MenuItem value="all">{t('orderManagementPage.all')}</MenuItem>
              <MenuItem value="pending">
                {t('orderManagementPage.pending')}
              </MenuItem>
              <MenuItem value="confirmed">
                {t('orderManagementPage.confirmed')}
              </MenuItem>
              <MenuItem value="completed">
                {t('orderManagementPage.completed')}
              </MenuItem>
              <MenuItem value="cancelled">
                {t('orderManagementPage.cancelled')}
              </MenuItem>
            </Select>
          </FormControl>
          <TextField
            type="date"
            label={t('orderManagementPage.startDate')}
            value={startDate}
            onChange={handleStartDateChange}
            InputLabelProps={{
              shrink: true
            }}
          />
          <TextField
            type="date"
            label={t('orderManagementPage.endDate')}
            value={endDate}
            onChange={handleEndDateChange}
            InputLabelProps={{
              shrink: true
            }}
          />
          <Button
            onClick={handleResetFilters}
            variant="outlined"
            sx={{ height: '56px' }}
          >
            {t('orderManagementPage.resetFilters')}
          </Button>
        </Toolbar>
        <TableContainer sx={{ flex: 1, overflow: 'auto' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('orderManagementPage.orderId')}</TableCell>
                <TableCell
                  sortDirection={orderBy === 'recipient_name' ? order : false}
                >
                  <TableSortLabel
                    active={orderBy === 'recipient_name'}
                    direction={orderBy === 'recipient_name' ? order : 'asc'}
                    onClick={(e) => handleRequestSort(e, 'recipient_name')}
                  >
                    {t('orderManagementPage.recipientName')}
                  </TableSortLabel>
                </TableCell>
                <TableCell>{t('orderManagementPage.totalAmount')}</TableCell>
                <TableCell>{t('orderManagementPage.status')}</TableCell>
                <TableCell>{t('orderManagementPage.paymentStatus')}</TableCell>
                <TableCell
                  sortDirection={orderBy === 'created_at' ? order : false}
                >
                  <TableSortLabel
                    active={orderBy === 'created_at'}
                    direction={orderBy === 'created_at' ? order : 'asc'}
                    onClick={(e) => handleRequestSort(e, 'created_at')}
                  >
                    {t('orderManagementPage.createdAt')}
                  </TableSortLabel>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredOrders
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((row) => (
                  <TableRow
                    key={row.order_id}
                    hover
                    onClick={() => handleOrderClick(row)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>{row.order_id.slice(-6)}</TableCell>
                    <TableCell>{row.recipient_name}</TableCell>
                    <TableCell>{row.total_amount}</TableCell>
                    <TableCell>{row.status}</TableCell>
                    <TableCell>{row.payment_status}</TableCell>
                    <TableCell>
                      {new Date(row.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[]}
          component="div"
          count={filteredOrders.length}
          rowsPerPage={8}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Order Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleDialogClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t('orderManagementPage.orderDetails')}</DialogTitle>
        <DialogContent>
          {selectedOrder && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="h6" gutterBottom>
                {t('orderManagementPage.basicInfo')}
              </Typography>
              <Grid2 container spacing={2} sx={{ mb: 3 }}>
                <Grid2 size={{ xs: 12, sm: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('orderManagementPage.orderId')}
                  </Typography>
                  <Typography variant="body1">
                    {selectedOrder.order_id}
                  </Typography>
                </Grid2>
                <Grid2 size={{ xs: 12, sm: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('orderManagementPage.recipientName')}
                  </Typography>
                  <Typography variant="body1">
                    {selectedOrder.recipient_name}
                  </Typography>
                </Grid2>
                <Grid2 size={{ xs: 12, sm: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('orderManagementPage.recipientPhone')}
                  </Typography>
                  <Typography variant="body1">
                    {selectedOrder.recipient_phone}
                  </Typography>
                </Grid2>
                <Grid2 size={{ xs: 12, sm: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('orderManagementPage.shippingAddress')}
                  </Typography>
                  <Typography variant="body1">
                    {selectedOrder.shipping_address}
                  </Typography>
                </Grid2>
              </Grid2>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                {t('orderManagementPage.statusAndPayment')}
              </Typography>
              <Grid2 container spacing={2} sx={{ mb: 3 }}>
                <Grid2 size={{ xs: 12, sm: 4 }}>
                  <FormControl fullWidth>
                    <InputLabel>{t('orderManagementPage.status')}</InputLabel>
                    <Select
                      value={editForm.status || ''}
                      label={t('orderManagementPage.status')}
                      onChange={(e) =>
                        handleFormChange(
                          'status',
                          e.target.value as UpdateOrderRequest['status']
                        )
                      }
                    >
                      <MenuItem value="pending">
                        {t('orderManagementPage.pending')}
                      </MenuItem>
                      <MenuItem value="confirmed">
                        {t('orderManagementPage.confirmed')}
                      </MenuItem>
                      <MenuItem value="completed">
                        {t('orderManagementPage.completed')}
                      </MenuItem>
                      <MenuItem value="cancelled">
                        {t('orderManagementPage.cancelled')}
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid2>
                <Grid2 size={{ xs: 12, sm: 4 }}>
                  <FormControl fullWidth>
                    <InputLabel>
                      {t('orderManagementPage.paymentStatus')}
                    </InputLabel>
                    <Select
                      value={editForm.payment_status || ''}
                      label={t('orderManagementPage.paymentStatus')}
                      onChange={(e) =>
                        handleFormChange(
                          'payment_status',
                          e.target.value as UpdateOrderRequest['payment_status']
                        )
                      }
                    >
                      <MenuItem value="paid">
                        {t('orderManagementPage.paid')}
                      </MenuItem>
                      <MenuItem value="unpaid">
                        {t('orderManagementPage.unpaid')}
                      </MenuItem>
                      <MenuItem value="refunded">
                        {t('orderManagementPage.refunded')}
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid2>
                <Grid2 size={{ xs: 12, sm: 4 }}>
                  <TextField
                    label={t('orderManagementPage.trackingNumber')}
                    value={editForm.tracking_number || ''}
                    onChange={(e) =>
                      handleFormChange('tracking_number', e.target.value)
                    }
                    fullWidth
                  />
                </Grid2>
              </Grid2>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                {t('orderManagementPage.items')}
              </Typography>
              {selectedOrder.items.map((item, index) => {
                const product = products.find(
                  (p) => p.product_id === item.product_id
                )
                const primaryImage = product?.images?.find(
                  (img) => img.is_primary
                )?.image_url

                return (
                  <Box
                    key={index}
                    sx={{ display: 'flex', alignItems: 'center', mb: 2 }}
                  >
                    {primaryImage && (
                      <Box
                        component="img"
                        src={primaryImage}
                        alt={product?.product_name}
                        sx={{
                          width: 50,
                          height: 50,
                          mr: 2,
                          objectFit: 'cover',
                          borderRadius: 1
                        }}
                      />
                    )}
                    <Box>
                      <Typography variant="body1">
                        {product
                          ? product.product_name
                          : `${t('orderManagementPage.productId')}: ${
                              item.product_id
                            }`}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('orderManagementPage.variantId')}: {item.variant_id}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('orderManagementPage.quantity')}: {item.quantity}
                      </Typography>
                    </Box>
                  </Box>
                )
              })}

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                {t('orderManagementPage.notes')}
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {selectedOrder.notes || t('common.noData')}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>{t('common.cancel')}</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </StyledOrderManagementPage>
  )
}

export default OrderManagementPage
