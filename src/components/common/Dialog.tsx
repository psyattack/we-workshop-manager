import * as RadixDialog from "@radix-ui/react-dialog";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
}

const SIZES: Record<NonNullable<DialogProps["size"]>, string> = {
  sm: "max-w-md",
  md: "max-w-2xl",
  lg: "max-w-4xl",
  xl: "max-w-6xl",
};

export default function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  size = "md",
}: DialogProps) {
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
                className="fixed inset-0 z-40 bg-background/70 backdrop-blur-sm"
              />
            </RadixDialog.Overlay>
            <RadixDialog.Content
              asChild
              onOpenAutoFocus={(e) => e.preventDefault()}
            >
              <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4">
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.97 }}
                  transition={{ duration: 0.18, ease: [0.2, 0.8, 0.2, 1] }}
                  className={cn(
                    "pointer-events-auto relative flex max-h-[calc(100vh-2rem)] w-full flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-2xl",
                    SIZES[size],
                  )}
                >
                  <div className="flex items-start justify-between border-b border-border bg-surface-raised/40 px-5 py-3.5">
                    <div className="min-w-0">
                      <RadixDialog.Title className="truncate text-sm font-semibold tracking-tight">
                        {title}
                      </RadixDialog.Title>
                      {description && (
                        <RadixDialog.Description className="mt-0.5 text-xs text-muted">
                          {description}
                        </RadixDialog.Description>
                      )}
                    </div>
                    <RadixDialog.Close
                      className="btn-icon -mr-1 -mt-1"
                      aria-label="Close"
                    >
                      <X className="h-4 w-4" />
                    </RadixDialog.Close>
                  </div>
                  <div className="min-h-0 flex-1 overflow-auto px-5 py-4">
                    {children}
                  </div>
                  {footer && (
                    <div className="flex items-center justify-end gap-2 border-t border-border bg-surface-sunken px-5 py-3">
                      {footer}
                    </div>
                  )}
                </motion.div>
              </div>
            </RadixDialog.Content>
          </RadixDialog.Portal>
        )}
      </AnimatePresence>
    </RadixDialog.Root>
  );
}
