import { Fragment, useMemo } from "react";

/**
 * Tiny, dependency-free markdown renderer just powerful enough for
 * GitHub release notes (which is the only place this is used). Supports:
 *
 *   - `# / ## / ### …` headings
 *   - `- ` and `* ` unordered list bullets
 *   - `1.` ordered list bullets
 *   - `> ` block quotes
 *   - fenced code blocks (```)
 *   - inline `code`, **bold**, *italic*, [text](url), bare URLs
 *   - horizontal rule (`---`)
 *
 * We deliberately escape HTML before parsing so a malicious release-notes
 * payload can't inject markup. Output is plain React nodes — no
 * `dangerouslySetInnerHTML`.
 */
export default function Markdown({ source }: { source: string }) {
  const blocks = useMemo(() => parseBlocks(source ?? ""), [source]);
  return (
    <div className="prose-markdown text-sm leading-relaxed">
      {blocks.map((b, i) => (
        <Fragment key={i}>{renderBlock(b, i)}</Fragment>
      ))}
    </div>
  );
}

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "para"; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "code"; lang?: string; text: string }
  | { type: "quote"; text: string }
  | { type: "hr" };

function parseBlocks(src: string): Block[] {
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const out: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    // fenced code block
    const fence = /^```\s*(\S*)\s*$/.exec(line);
    if (fence) {
      const lang = fence[1] || undefined;
      i++;
      const buf: string[] = [];
      while (i < lines.length && !/^```\s*$/.test(lines[i])) {
        buf.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      out.push({ type: "code", lang, text: buf.join("\n") });
      continue;
    }
    // hr
    if (/^\s*(---|\*\*\*|___)\s*$/.test(line)) {
      out.push({ type: "hr" });
      i++;
      continue;
    }
    // heading
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) {
      out.push({ type: "heading", level: h[1].length, text: h[2] });
      i++;
      continue;
    }
    // unordered list
    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i++;
      }
      out.push({ type: "list", ordered: false, items });
      continue;
    }
    // ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      out.push({ type: "list", ordered: true, items });
      continue;
    }
    // quote
    if (/^>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        buf.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      out.push({ type: "quote", text: buf.join("\n") });
      continue;
    }
    // blank
    if (!line.trim()) {
      i++;
      continue;
    }
    // paragraph (consume until blank)
    const buf: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^(#{1,6})\s/.test(lines[i]) &&
      !/^```/.test(lines[i]) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !/^>\s?/.test(lines[i]) &&
      !/^\s*(---|\*\*\*|___)\s*$/.test(lines[i])
    ) {
      buf.push(lines[i]);
      i++;
    }
    out.push({ type: "para", text: buf.join(" ") });
  }
  return out;
}

function renderBlock(b: Block, idx: number) {
  switch (b.type) {
    case "heading": {
      const cls =
        b.level === 1
          ? "mt-3 text-base font-semibold"
          : b.level === 2
            ? "mt-3 text-sm font-semibold"
            : "mt-2 text-sm font-semibold text-subtle";
      return <div className={cls}>{renderInline(b.text)}</div>;
    }
    case "para":
      return (
        <p className="mb-2 mt-1 text-sm">{renderInline(b.text)}</p>
      );
    case "list":
      if (b.ordered) {
        return (
          <ol className="mb-2 ml-5 list-decimal space-y-0.5 text-sm">
            {b.items.map((it, i) => (
              <li key={i}>{renderInline(it)}</li>
            ))}
          </ol>
        );
      }
      return (
        <ul className="mb-2 ml-5 list-disc space-y-0.5 text-sm">
          {b.items.map((it, i) => (
            <li key={i}>{renderInline(it)}</li>
          ))}
        </ul>
      );
    case "code":
      return (
        <pre
          key={idx}
          className="mb-2 max-h-72 overflow-auto rounded-md border border-border bg-surface-sunken px-3 py-2 text-xs"
        >
          <code>{b.text}</code>
        </pre>
      );
    case "quote":
      return (
        <blockquote className="mb-2 border-l-2 border-border-strong pl-3 text-sm italic text-muted">
          {renderInline(b.text)}
        </blockquote>
      );
    case "hr":
      return <hr className="my-3 border-border" />;
  }
}

function renderInline(text: string): React.ReactNode {
  // tokenize: code, bold, italic, links, bare URLs, raw text
  const out: React.ReactNode[] = [];
  let rest = text;
  let key = 0;
  const push = (n: React.ReactNode) => {
    out.push(<Fragment key={key++}>{n}</Fragment>);
  };
  while (rest.length) {
    // code `...`
    const code = /`([^`]+)`/.exec(rest);
    // bold **...** or __...__
    const bold = /\*\*([^*]+)\*\*|__([^_]+)__/.exec(rest);
    // italic *...* or _..._
    const ital = /(^|[^*])\*([^*\s][^*]*[^*\s]|[^*\s])\*/.exec(rest);
    // link [text](url)
    const link = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/.exec(rest);
    // bare http(s)://... URL
    const url = /https?:\/\/[^\s<>)]+/.exec(rest);

    const candidates = [
      { m: code, kind: "code" as const },
      { m: bold, kind: "bold" as const },
      { m: ital, kind: "ital" as const },
      { m: link, kind: "link" as const },
      { m: url, kind: "url" as const },
    ].filter((c) => c.m);
    if (candidates.length === 0) {
      push(rest);
      break;
    }
    candidates.sort((a, b) => (a.m!.index ?? 0) - (b.m!.index ?? 0));
    const first = candidates[0];
    const m = first.m!;
    const before = rest.slice(0, m.index);
    if (before) push(before);
    if (first.kind === "code") {
      push(
        <code className="rounded bg-surface-sunken px-1 py-0.5 font-mono text-[11px]">
          {m[1]}
        </code>,
      );
      rest = rest.slice((m.index ?? 0) + m[0].length);
    } else if (first.kind === "bold") {
      push(<strong className="font-semibold">{m[1] ?? m[2]}</strong>);
      rest = rest.slice((m.index ?? 0) + m[0].length);
    } else if (first.kind === "ital") {
      push(m[1]);
      push(<em className="italic">{m[2]}</em>);
      rest = rest.slice((m.index ?? 0) + m[0].length);
    } else if (first.kind === "link") {
      push(
        <a
          href={m[2]}
          target="_blank"
          rel="noreferrer"
          className="text-primary hover:underline"
        >
          {m[1]}
        </a>,
      );
      rest = rest.slice((m.index ?? 0) + m[0].length);
    } else {
      push(
        <a
          href={m[0]}
          target="_blank"
          rel="noreferrer"
          className="text-primary hover:underline"
        >
          {m[0]}
        </a>,
      );
      rest = rest.slice((m.index ?? 0) + m[0].length);
    }
  }
  return out;
}
