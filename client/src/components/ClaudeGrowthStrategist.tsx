import React, { useState, useRef, useEffect } from "react";
import {
  Sparkles,
  Send,
  User,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Brain,
  Wrench,
} from "lucide-react";
import { chatWithGrowthAgent } from "@/services/api";
import { ChatMessage } from "@/types";

interface ClaudeGrowthStrategistProps {
  merchantId: string;
  sessionId: string;
}

// Markdown parser that strips codeblock fences, unwraps JSON, and formats bold & inline code
const parseMarkdown = (rawText: string): React.ReactNode => {
  if (!rawText) return null;
  let text = String(rawText);

  // Strip markdown code fences if wrapped
  text = text.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();

  // If the text is a serialized JSON object, unwrap reply
  if (text.startsWith("{") && text.includes('"reply"')) {
    try {
      const parsed = JSON.parse(text);
      if (parsed.reply) text = parsed.reply;
    } catch {
      const match = text.match(/"reply"\s*:\s*"([^"]+)"/);
      if (match && match[1]) text = match[1];
    }
  }

  // Strip any leftover triple or double backticks
  text = text.replace(/```[a-z]*/gi, "").replace(/```/g, "").replace(/``/g, "").trim();

  // Parse inline bold (**bold**) and inline code (`code`)
  const parts: React.ReactNode[] = [];
  // Tokenize by bold **...** or inline code `...`
  const tokenRegex = /(\*\*.*?\*\*|`[^`]+`)/g;
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = tokenRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const token = match[1];
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={`b-${key++}`} className="font-semibold text-[var(--text-primary)]">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code
          key={`c-${key++}`}
          className="px-1.5 py-0.5 mx-0.5 rounded-md bg-[var(--bg-card)] border border-[var(--border-subtle)] font-mono text-[11px] text-[var(--accent-terracotta)] font-medium"
        >
          {token.slice(1, -1)}
        </code>
      );
    }
    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
};

export const ClaudeGrowthStrategist: React.FC<ClaudeGrowthStrategistProps> = ({
  merchantId,
  sessionId,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg_1",
      role: "ai",
      content:
        "Hello! I am your autonomous RazorGrowth Manager. I continuously inspect your live session trace, customer cohorts, and A/B experiments. Ask me anything about your revenue opportunities or growth strategies!",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedReasoningIds, setExpandedReasoningIds] = useState<Set<string>>(new Set());
  const [expandedToolIds, setExpandedToolIds] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    "who payed for which opportunities",
    "Why was this audience count selected?",
    "What experiments were run and what was the lift?",
    "📊 Cross-reference with past session benchmarks",
    "Explain agent reasoning step-by-step.",
    "Why did you choose this offer code?",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const toggleReasoning = (id: string) => {
    setExpandedReasoningIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleTools = (id: string) => {
    setExpandedToolIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSend = async (queryText?: string) => {
    const text = (queryText || inputQuery).trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const res = await chatWithGrowthAgent(
        merchantId || "merch_demo",
        text,
        sessionId
      );

      let replyContent = res.reply;
      let followUp = res.suggested_action || res.suggested_follow_up;

      // Clean serialized JSON if returned directly by LLM
      if (typeof replyContent === "string" && replyContent.trim().startsWith("{") && replyContent.includes('"reply"')) {
        try {
          const parsed = JSON.parse(replyContent.trim());
          if (parsed.reply) replyContent = parsed.reply;
          if (parsed.suggested_follow_up_action || parsed.suggested_action) {
            followUp = parsed.suggested_follow_up_action || parsed.suggested_action;
          }
        } catch {}
      }

      const aiMsg: ChatMessage = {
        id: `ai_${Date.now()}`,
        role: "ai",
        content: replyContent,
        suggestedAction: followUp,
        reasoning_trace: res.reasoning_trace,
        provider_used: res.provider_used || "nvidia_nim",
        tools_used: res.tools_used || [],
        tool_data: res.tool_data || {},
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, aiMsg]);
      if (res.reasoning_trace) {
        setExpandedReasoningIds((prev) => new Set(prev).add(aiMsg.id));
      }
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: `ai_err_${Date.now()}`,
        role: "ai",
        content:
          "I am analyzing your merchant session trace. Please generate a new session or run a growth scan first to enrich my context!",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-[var(--shadow-sm)] flex flex-col h-[650px] max-w-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[var(--accent-terracotta)] text-white flex items-center justify-center font-serif text-base font-bold shadow-sm">
            ✦
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-serif text-base font-semibold text-[var(--text-primary)]">
                AI Growth Strategist
              </h3>
              <span className="px-2 py-0.5 bg-[var(--accent-terracotta-subtle)] text-[var(--accent-terracotta)] rounded-full text-[10px] font-semibold">
                ACTIVE
              </span>
            </div>
            <span className="text-[11px] text-[var(--text-muted)] font-mono block mt-0.5">
              Active Context: {sessionId}
            </span>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto py-3.5 space-y-3.5 pr-1.5 min-h-0">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          const isReasoningOpen = expandedReasoningIds.has(msg.id);

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-2.5 ${
                isUser ? "flex-row-reverse" : "flex-row"
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                  isUser
                    ? "bg-[var(--accent-terracotta)] text-white"
                    : "bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[var(--accent-terracotta)]"
                }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : "✦"}
              </div>

              {/* Message Bubble */}
              <div
                className={`flex-1 max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed transition-all shadow-xs ${
                  isUser
                    ? "bg-[var(--accent-terracotta)] text-white rounded-tr-none"
                    : "bg-[var(--bg-secondary)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-tl-none"
                }`}
              >
                {/* Model Reasoning Trace (Collapsible) */}
                {!isUser && msg.reasoning_trace && (
                  <div className="mb-2.5 p-2.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)]">
                    <button
                      onClick={() => toggleReasoning(msg.id)}
                      className="flex items-center justify-between w-full text-[11px] font-semibold text-[var(--accent-terracotta)] hover:opacity-80 transition-opacity cursor-pointer"
                    >
                      <div className="flex items-center gap-1.5">
                        <Brain className="w-3.5 h-3.5" />
                        <span>Thinking Process / Reasoning Trace</span>
                      </div>
                      {isReasoningOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    {isReasoningOpen && (
                      <p className="mt-2 text-[11px] text-[var(--text-muted)] font-mono leading-relaxed border-t border-[var(--border-subtle)] pt-2">
                        {msg.reasoning_trace}
                      </p>
                    )}
                  </div>
                )}

                {/* Agent Tools Used Dropdown (Collapsible) */}
                {!isUser && msg.tools_used && msg.tools_used.length > 0 && (
                  <div className="mb-2.5 p-2.5 rounded-xl bg-[var(--bg-card)] border border-emerald-500/20">
                    <button
                      onClick={() => toggleTools(msg.id)}
                      className="flex items-center justify-between w-full text-[11px] font-semibold text-[var(--accent-emerald)] hover:opacity-80 transition-opacity cursor-pointer"
                    >
                      <div className="flex items-center gap-1.5">
                        <Wrench className="w-3.5 h-3.5" />
                        <span>
                          Tools Invoked ({msg.tools_used.length}): {msg.tools_used.join(", ")}
                        </span>
                      </div>
                      {expandedToolIds.has(msg.id) ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedToolIds.has(msg.id) && msg.tool_data && (
                      <div className="mt-2 text-[10px] text-[var(--text-secondary)] font-mono max-h-48 overflow-y-auto bg-[var(--bg-secondary)] p-2.5 rounded-lg border border-[var(--border-subtle)] whitespace-pre-wrap leading-relaxed">
                        {JSON.stringify(msg.tool_data, null, 2)}
                      </div>
                    )}
                  </div>
                )}

                {/* Main Message Content - Parsed for bold text */}
                <div className="whitespace-pre-wrap leading-relaxed break-words">
                  {!isUser ? parseMarkdown(msg.content) : msg.content}
                </div>

                {/* Suggested Action Button (if any) */}
                {msg.suggestedAction && (
                  <div className="mt-2.5 pt-2 border-t border-black/5 dark:border-white/10 flex items-center gap-2">
                    <button
                      onClick={() => handleSend(msg.suggestedAction)}
                      className="text-[11px] font-semibold text-[var(--accent-terracotta)] hover:underline flex items-center gap-1.5 cursor-pointer"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>{msg.suggestedAction}</span>
                    </button>
                  </div>
                )}

                {/* Timestamp & Copy */}
                <div
                  className={`flex items-center justify-between mt-2.5 pt-1.5 text-[10px] ${
                    isUser ? "text-white/70" : "text-[var(--text-muted)]"
                  }`}
                >
                  <span>{msg.timestamp}</span>
                  <button
                    onClick={() => handleCopy(msg.id, msg.content)}
                    className="hover:opacity-100 opacity-60 transition-opacity p-0.5 cursor-pointer"
                    title="Copy message"
                  >
                    {copiedId === msg.id ? (
                      <Check className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-2.5 text-xs text-[var(--text-muted)] pl-9 py-1">
            <span className="w-2 h-2 rounded-full bg-[var(--accent-terracotta)] animate-ping" />
            <span>AI Growth Strategist is synthesizing session reasoning...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips */}
      <div className="py-2.5 border-t border-[var(--border-subtle)] flex items-center gap-2 overflow-x-auto no-scrollbar shrink-0">
        {quickPrompts.map((prompt) => (
          <button
            key={prompt}
            onClick={() => handleSend(prompt)}
            disabled={isLoading}
            className="px-3 py-1.5 rounded-full text-[11px] font-medium bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] shrink-0 transition-colors cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="pt-2 flex items-center gap-2 shrink-0"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask about customer cohorts, lift metrics, or opportunity reasoning..."
          disabled={isLoading}
          className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] focus:border-[var(--accent-terracotta)] focus:ring-1 focus:ring-[var(--accent-terracotta)]/30 rounded-xl px-4 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none transition-all"
        />
        <button
          type="submit"
          disabled={!inputQuery.trim() || isLoading}
          className="w-10 h-10 rounded-xl bg-[var(--accent-terracotta)] hover:bg-[var(--accent-terracotta-hover)] text-white flex items-center justify-center transition-all disabled:opacity-40 cursor-pointer shrink-0 shadow-sm"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
