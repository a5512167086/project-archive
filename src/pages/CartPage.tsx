import { useSelector, useDispatch } from "react-redux";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  removeFromCart,
  updateQuantity,
  clearCart,
} from "@/store/modules/cartSlice";
import { RootState } from "@/store";
import { Trash2 } from "lucide-react";
import {
  useGetProductsQuery,
  useCreateOrderMutation,
  type Product,
} from "@/store/apis/ecommApi";
import { useLiff } from "@/hooks/useLiff";
import { useNavigate } from "react-router";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/useToast";

const getCartItemPrice = (
  product: Product,
  variantId: string | null | undefined
) => {
  if (variantId) {
    const variant = product.variants?.find((v) => v.variant_id === variantId);
    if (variant) {
      return variant.price;
    }
  }
  return product.price;
};

export function CartPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { toast } = useToast();
  const { botUUID } = useLiff();
  const { data: products, isLoading } = useGetProductsQuery(botUUID || "", {
    skip: !botUUID,
  });

  const cartItems = useSelector((state: RootState) => state.cart.items);

  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [recipientName, setRecipientName] = useState("");
  const [recipientPhone, setRecipientPhone] = useState("");
  const [note, setNote] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [shippingMethod, setShippingMethod] = useState("store_pickup");
  const [shippingAddress, setShippingAddress] = useState("");

  if (isLoading) {
    return <div>Loading...</div>;
  }

  const cartProducts = cartItems
    .map((item) => {
      const product = products?.find((p) => p.product_id === item.productId);
      if (!product) return null;
      return {
        ...item,
        product,
      };
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);

  const cartTotal = cartProducts.reduce(
    (total, item) =>
      total + getCartItemPrice(item.product, item.variantId) * item.quantity,
    0
  );

  const handleRemove = (itemId: string) => {
    dispatch(removeFromCart({ itemId }));
  };

  const handleQuantityChange = (itemId: string, quantity: number) => {
    if (quantity > 0) {
      dispatch(updateQuantity({ itemId, quantity }));
    } else {
      dispatch(removeFromCart({ itemId }));
    }
  };

  const [createOrder, { isLoading: isCreatingOrder }] =
    useCreateOrderMutation();

  const handlePurchase = async () => {
    if (!botUUID) {
      console.error("botUUID is not available");
      return;
    }
    const orderItems = cartProducts
      .map((item) => {
        if (item.variantId !== null && item.variantId !== undefined) {
          const variantExists = item.product.variants?.some(
            (v) => v.variant_id === item.variantId
          );
          if (!variantExists) {
            return null;
          }
        }

        return {
          product_id: item.productId,
          variant_id: item.variantId ?? null,
          quantity: item.quantity,
        };
      })
      .filter((item): item is NonNullable<typeof item> => item !== null);

    if (orderItems.length !== cartProducts.length) {
      console.warn(
        "Some items in the cart were removed from the order because they were missing a variant selection or the selected variant is no longer available."
      );
    }

    if (orderItems.length === 0) {
      console.error("No items to purchase.");
      // TODO: Show toast
      return;
    }

    try {
      await createOrder({
        bot_uuid: botUUID,
        recipient_name: recipientName,
        recipient_phone: recipientPhone,
        notes: note,
        payment_method: paymentMethod as "cash" | "bank_transfer",
        shipping_method: shippingMethod as "home_delivery" | "store_pickup",
        shipping_address:
          shippingMethod === "home_delivery" ? shippingAddress : undefined,
        items: orderItems,
      }).unwrap();

      dispatch(clearCart());
      setIsCheckoutOpen(false);
      navigate("/orders");
      toast.success("訂單已成功建立！感謝您的購買。");
    } catch (err) {
      console.error("Failed to create order:", err);
      // TODO: Show error toast
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">購物車</h1>
      {cartProducts.length === 0 ? (
        <p>你的購物車是空的</p>
      ) : (
        <div className="space-y-4">
          {cartProducts.map((item) => (
            <Card key={item.itemId}>
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <img
                    src={item.product.images?.[0]?.image_url || ""}
                    alt={item.product.product_name}
                    className="w-16 h-16 object-cover rounded"
                  />
                  <div>
                    <p className="font-semibold">{item.product.product_name}</p>
                    <p className="text-sm text-gray-500">
                      ${getCartItemPrice(item.product, item.variantId)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    value={item.quantity}
                    onChange={(e) =>
                      handleQuantityChange(
                        item.itemId,
                        parseInt(e.target.value)
                      )
                    }
                    className="w-16 text-center border rounded"
                    min="1"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemove(item.itemId)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>訂單摘要</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-2">
          <div className="flex justify-between">
            <span>小計</span>
            <span>${cartTotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-bold mt-2">
            <span>總計</span>
            <span>${cartTotal.toFixed(2)}</span>
          </div>
          <Button
            variant="link"
            className="w-full mt-4"
            onClick={() => navigate("/home?module=ecommerce")}
          >
            繼續購物
          </Button>
          <Dialog open={isCheckoutOpen} onOpenChange={setIsCheckoutOpen}>
            <DialogTrigger asChild>
              <Button
                className="w-full mt-4"
                disabled={cartProducts.length === 0}
              >
                前往結帳
              </Button>
            </DialogTrigger>
            <DialogContent className="h-full w-full max-w-none flex flex-col">
              <DialogHeader>
                <DialogTitle>結帳</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label htmlFor="name">收件人姓名</Label>
                  <Input
                    id="name"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="phone">收件人電話</Label>
                  <Input
                    id="phone"
                    value={recipientPhone}
                    onChange={(e) => setRecipientPhone(e.target.value)}
                  />
                </div>
                <div>
                  <Label>配送方式</Label>
                  <Select
                    onValueChange={setShippingMethod}
                    defaultValue={shippingMethod}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="選擇配送方式" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="store_pickup">門市取貨</SelectItem>
                      <SelectItem value="home_delivery">宅配</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {shippingMethod === "home_delivery" && (
                  <div>
                    <Label htmlFor="address">配送地址</Label>
                    <Input
                      id="address"
                      value={shippingAddress}
                      onChange={(e) => setShippingAddress(e.target.value)}
                    />
                  </div>
                )}
                <div>
                  <Label>付款方式</Label>
                  <Select
                    onValueChange={setPaymentMethod}
                    defaultValue={paymentMethod}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="選擇付款方式" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">現金</SelectItem>
                      <SelectItem value="bank_transfer">銀行轉帳</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="note">備註</Label>
                  <Textarea
                    id="note"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button onClick={handlePurchase} disabled={isCreatingOrder}>
                  {isCreatingOrder ? "下單中..." : "確認下單"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
