import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useState, useEffect } from "react";

interface Props {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
  infoText?: string;
}

export default function Pagination({ page, totalPages, onChange, infoText }: Props) {
  const { t } = useTranslation();
  const safeTotal = Math.max(1, totalPages || 1);
  const hasPrev = page > 1;
  const hasNext = page < safeTotal;
  const [inputValue, setInputValue] = useState(String(page));

  useEffect(() => {
    setInputValue(String(page));
  }, [page]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleInputBlur = () => {
    const num = parseInt(inputValue, 10);
    if (!isNaN(num) && num >= 1 && num <= safeTotal) {
      onChange(num);
    } else {
      setInputValue(String(page));
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleInputBlur();
    }
  };

  return (
    <div className="flex items-center justify-between gap-2 border-t border-border bg-surface/60 px-4">
      <div className="flex-1 text-xs text-muted">
        {infoText || ""}
      </div>
      <div className="flex items-center gap-2">
        <button className="btn-icon" disabled={!hasPrev} onClick={() => onChange(1)}>
          <ChevronsLeft className="h-4 w-4" />
        </button>
        <button
          className="btn-icon"
          disabled={!hasPrev}
          onClick={() => onChange(page - 1)}
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <div className="flex items-center gap-1 px-16 text-xs text-muted">
          {t("labels.page")}{" "}
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onKeyDown={handleInputKeyDown}
            className="w-9 bg-transparent px-1 text-center text-foreground focus:outline-none"
          />{" "}
          {t("labels.of", { total: safeTotal })}
        </div>
        <button
          className="btn-icon"
          disabled={!hasNext}
          onClick={() => onChange(page + 1)}
        >
          <ChevronRight className="h-4 w-4" />
        </button>
        <button
          className="btn-icon"
          disabled={!hasNext}
          onClick={() => onChange(safeTotal)}
        >
          <ChevronsRight className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1"></div>
    </div>
  );
}
