import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Clipboard, Check } from "lucide-react";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface Props { content: string; }

const fencedCodePattern = /(```[\s\S]*?```|~~~[\s\S]*?~~~)/g;

/** Convert the bracket delimiters commonly emitted by local models to remark-math syntax.
 * Fenced code is kept untouched so examples containing LaTeX remain code.
 */
function normalizeMathDelimiters(content: string) {
  return content
    .split(fencedCodePattern)
    .map((part, index) => {
      if (index % 2 === 1) return part;
      return part
        .replace(/\\\[([\s\S]*?)\\\]/g, (_, math: string) => `\n\n$$\n${math.trim()}\n$$\n\n`)
        .replace(/\\\(([\s\S]*?)\\\)/g, (_, math: string) => `$${math}$`);
    })
    .join("");
}

function CodeBlock({ language, value }: { language: string; value: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard?.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };
  return (
    <div className="code-block">
      <div className="code-header">
        <span>{language || "text"}</span>
        <button type="button" onClick={copy} aria-label="Copy code">
          {copied ? <Check size={13} /> : <Clipboard size={13} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter language={language || "text"} style={oneDark} customStyle={{ background: "transparent" }}>
        {value}
      </SyntaxHighlighter>
    </div>
  );
}

export function MarkdownRenderer({ content }: Props) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[[rehypeKatex, { throwOnError: false, strict: false, errorColor: "#ff7e91" }]]}
      skipHtml
      components={{
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className ?? "");
          const value = String(children).replace(/\n$/, "");
          return match ? <CodeBlock language={match[1]} value={value} /> : <code className={className} {...props}>{children}</code>;
        },
        a({ children, ...props }) { return <a {...props} target="_blank" rel="noreferrer">{children}</a>; },
      }}
    >
      {normalizeMathDelimiters(content)}
    </ReactMarkdown>
  );
}
