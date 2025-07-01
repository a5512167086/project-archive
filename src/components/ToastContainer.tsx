import { useToast } from "../hooks/useToast";
import { Toast, ToastClose, ToastDescription, ToastTitle } from "./ui/toast";

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[100] flex flex-col items-center space-y-2 p-4 pointer-events-none">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          variant={toast.variant}
          className="pointer-events-auto max-w-sm w-full animate-in slide-in-from-bottom-2"
        >
          <div className="grid gap-1">
            {toast.title && <ToastTitle>{toast.title}</ToastTitle>}
            {toast.description && (
              <ToastDescription>{toast.description}</ToastDescription>
            )}
          </div>
          <ToastClose onClick={() => removeToast(toast.id)} />
        </Toast>
      ))}
    </div>
  );
}
