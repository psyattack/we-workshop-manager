import * as RadixTabs from "@radix-ui/react-tabs";
import { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface TabItem {
  value: string;
  label: ReactNode;
  content: ReactNode;
}

interface Props {
  value: string;
  onValueChange: (v: string) => void;
  items: TabItem[];
  className?: string;
}

export default function Tabs({ value, onValueChange, items, className }: Props) {
  return (
    <RadixTabs.Root
      value={value}
      onValueChange={onValueChange}
      className={cn("flex h-full flex-col", className)}
    >
      <RadixTabs.List className="flex gap-1 border-b border-border px-1">
        {items.map((item) => (
          <RadixTabs.Trigger
            key={item.value}
            value={item.value}
            className="relative rounded-t-md px-3 py-2 text-sm text-muted transition-colors hover:text-foreground data-[state=active]:text-foreground"
          >
            {item.label}
            <span className="absolute bottom-0 left-1/2 h-0.5 w-6 -translate-x-1/2 scale-x-0 rounded-full bg-primary transition-transform data-[state=active]:scale-x-100" />
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      <div className="flex-1 overflow-auto">
        {items.map((item) => (
          <RadixTabs.Content
            key={item.value}
            value={item.value}
            className="h-full outline-none"
          >
            {item.content}
          </RadixTabs.Content>
        ))}
      </div>
    </RadixTabs.Root>
  );
}
