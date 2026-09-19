import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Clipboard, Check } from "lucide-react";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface Props { content: string; }

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
      remarkPlugins={[remarkGfm]}
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
      {content}
    </ReactMarkdown>
  );
}

