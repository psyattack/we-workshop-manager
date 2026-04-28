import * as RadixDialog from "@radix-ui/react-dialog";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface DrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: ReactNode;
  children: ReactNode;
  side?: "right" | "left";
  width?: string;
}

export default function Drawer({
  open,
  onOpenChange,
  title,
  children,
  side = "right",
  width = "420px",
}: DrawerProps) {
  const isRight = side === "right";
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
                className="fixed inset-0 z-40 bg-background/60 backdrop-blur-[2px]"
              />
            </RadixDialog.Overlay>
            <RadixDialog.Content asChild>
              <motion.aside
                initial={{ x: isRight ? "100%" : "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: isRight ? "100%" : "-100%" }}
                transition={{
                  type: "spring",
                  stiffness: 380,
                  damping: 36,
                }}
                style={{ width }}
                className={cn(
                  "fixed top-0 z-50 flex h-full flex-col border-border bg-surface shadow-card-hover",
                  isRight ? "right-0 border-l" : "left-0 border-r",
                )}
              >
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <RadixDialog.Title className="text-sm font-semibold">
                    {title}
                  </RadixDialog.Title>
                  <RadixDialog.Description className="sr-only">
                    {title}
                  </RadixDialog.Description>
                  <RadixDialog.Close className="btn-icon" aria-label="Close">
                    <X className="h-5 w-5" />
                  </RadixDialog.Close>
                </div>
                <div className="drawer-scroll flex-1 overflow-auto">
                  {children}
                </div>
              </motion.aside>
            </RadixDialog.Content>
          </RadixDialog.Portal>
        )}
      </AnimatePresence>
    </RadixDialog.Root>
  );
}
