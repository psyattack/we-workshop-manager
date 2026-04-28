import * as RadixDialog from "@radix-ui/react-dialog";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import { ReactNode } from "react";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  message: string | ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  variant?: "danger" | "warning" | "info";
}

export default function ConfirmDialog({
  open,
  onOpenChange,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  variant = "warning",
}: ConfirmDialogProps) {
  const handleConfirm = () => {
    onConfirm();
    onOpenChange(false);
  };

  const variantStyles = {
    danger: {
      icon: "text-danger",
      button: "bg-danger hover:bg-danger/90 text-white",
    },
    warning: {
      icon: "text-warning",
      button: "bg-warning hover:bg-warning/90 text-background",
    },
    info: {
      icon: "text-primary",
      button: "bg-primary hover:bg-primary/90 text-white",
    },
  };

  const styles = variantStyles[variant];

  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <AnimatePresence>
        {open && (
          <RadixDialog.Portal forceMount>
            <RadixDialog.Overlay asChild>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
              />
            </RadixDialog.Overlay>
            <RadixDialog.Content
              asChild
              onOpenAutoFocus={(e) => e.preventDefault()}
            >
              <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4">
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: 10 }}
                  transition={{ duration: 0.2, ease: [0.2, 0.8, 0.2, 1] }}
                  className="pointer-events-auto relative flex w-full max-w-md flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-2xl"
                >
                  <div className="flex items-start gap-3 px-5 py-4">
                    <div className={`mt-0.5 flex-shrink-0 ${styles.icon}`}>
                      <AlertTriangle className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <RadixDialog.Title className="text-base font-semibold leading-tight">
                        {title}
                      </RadixDialog.Title>
                      <RadixDialog.Description className="mt-2 whitespace-pre-line text-sm leading-relaxed text-muted">
                        {message}
                      </RadixDialog.Description>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 border-t border-border bg-surface-sunken px-5 py-3">
                    <button
                      type="button"
                      onClick={() => onOpenChange(false)}
                      className="rounded-md px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-raised"
                    >
                      {cancelLabel}
                    </button>
                    <button
                      type="button"
                      onClick={handleConfirm}
                      className={`rounded-md px-4 py-2 text-sm font-semibold shadow-sm transition-colors ${styles.button}`}
                    >
                      {confirmLabel}
                    </button>
                  </div>
                </motion.div>
              </div>
            </RadixDialog.Content>
          </RadixDialog.Portal>
        )}
      </AnimatePresence>
    </RadixDialog.Root>
  );
}
