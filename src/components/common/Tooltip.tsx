import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";

interface TooltipProps {
  children: ReactNode;
  content: string;
  side?: "top" | "bottom" | "left" | "right";
  delay?: number;
}

export function Tooltip({ children, content, side = "top", delay = 50 }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [mounted, setMounted] = useState(true);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<number>();

  const showTooltip = () => {
    if (!mounted) return;
    timeoutRef.current = window.setTimeout(() => {
      setVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setVisible(false);
    // Remount tooltip component to reset state
    setMounted(false);
    setTimeout(() => setMounted(true), 50);
  };

  useEffect(() => {
    if (visible && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      let x = 0;
      let y = 0;

      switch (side) {
        case "top":
          x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
          y = triggerRect.top - tooltipRect.height - 8;
          break;
        case "bottom":
          x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
          y = triggerRect.bottom + 8;
          break;
        case "left":
          x = triggerRect.left - tooltipRect.width - 8;
          y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
          break;
        case "right":
          x = triggerRect.right + 8;
          y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
          break;
      }

      // Keep tooltip within viewport
      const padding = 8;
      x = Math.max(padding, Math.min(x, window.innerWidth - tooltipRect.width - padding));
      y = Math.max(padding, Math.min(y, window.innerHeight - tooltipRect.height - padding));

      setPosition({ x, y });
    }
  }, [visible, side]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (!content) return <>{children}</>;

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="inline-flex"
      >
        {children}
      </div>

      {mounted && createPortal(
        <AnimatePresence>
          {visible && (
            <motion.div
              ref={tooltipRef}
              initial={{ opacity: 0, scale: 0.92, y: side === "top" ? 4 : side === "bottom" ? -4 : 0 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92 }}
              transition={{ duration: 0.12, ease: [0.16, 1, 0.3, 1] }}
              className="fixed z-[99999] pointer-events-none"
              style={{
                left: `${position.x}px`,
                top: `${position.y}px`,
              }}
            >
              <div className="relative">
                <div className="rounded-md bg-surface-raised/95 border border-border-strong px-3 py-1.5 text-xs font-medium text-foreground shadow-lg backdrop-blur-sm">
                  {content}
                </div>
                <div
                  className="absolute w-2 h-2 bg-surface-raised/95 border-border-strong"
                  style={{
                    ...(side === "top" && {
                      bottom: "-4px",
                      left: "50%",
                      transform: "translateX(-50%) rotate(45deg)",
                      borderRight: "1px solid rgb(var(--border-strong))",
                      borderBottom: "1px solid rgb(var(--border-strong))",
                      borderLeft: "none",
                      borderTop: "none",
                    }),
                    ...(side === "bottom" && {
                      top: "-4px",
                      left: "50%",
                      transform: "translateX(-50%) rotate(45deg)",
                      borderLeft: "1px solid rgb(var(--border-strong))",
                      borderTop: "1px solid rgb(var(--border-strong))",
                      borderRight: "none",
                      borderBottom: "none",
                    }),
                    ...(side === "left" && {
                      right: "-4px",
                      top: "50%",
                      transform: "translateY(-50%) rotate(45deg)",
                      borderTop: "1px solid rgb(var(--border-strong))",
                      borderRight: "1px solid rgb(var(--border-strong))",
                      borderLeft: "none",
                      borderBottom: "none",
                    }),
                    ...(side === "right" && {
                      left: "-4px",
                      top: "50%",
                      transform: "translateY(-50%) rotate(45deg)",
                      borderBottom: "1px solid rgb(var(--border-strong))",
                      borderLeft: "1px solid rgb(var(--border-strong))",
                      borderRight: "none",
                      borderTop: "none",
                    }),
                  }}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  );
}
