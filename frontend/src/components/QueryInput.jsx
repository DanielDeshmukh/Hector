import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Paperclip, CornerDownLeft, Mic, MicOff } from "lucide-react";

export default function QueryInput({
  onSubmit,
  isLoading,
  showSuggestions,
  suggestions = [],
}) {
  const [query, setQuery] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSpeechSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-IN";

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((result) => result[0].transcript)
          .join("");
        setQuery(transcript);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [query]);

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const toggleVoice = useCallback(() => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setQuery("");
      recognitionRef.current.start();
      setIsListening(true);
    }
  }, [isListening]);

  // Ctrl+K / Cmd+K keyboard shortcut to focus search
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        textareaRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, []);

  return (
    <div className="w-full">
      {showSuggestions && suggestions.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2 animate-fade-in-delay-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => {
                setQuery(suggestion);
                textareaRef.current?.focus();
              }}
              aria-label={`Use suggestion: ${suggestion}`}
              className="rounded-lg border border-slate-custom/50 bg-charcoal/50 px-3.5 py-2 text-[12.5px] text-silver transition-all hover:border-gold/30 hover:text-gold-light hover:bg-gold/5"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <div className="relative rounded-xl border border-slate-custom/60 bg-charcoal/80 transition-all focus-within:border-gold/40 focus-within:shadow-[0_0_0_1px_rgba(201,169,98,0.1)]">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Enter your legal query - e.g., "What is the BNS equivalent of IPC Section 302?"'
          rows={1}
          disabled={isLoading}
          aria-label="Legal search query"
          role="searchbox"
          className="w-full resize-none bg-transparent px-4 pt-4 pb-12 text-[14.5px] text-gold-light placeholder-silver/40 outline-none disabled:opacity-50"
        />

        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 py-2.5">
          <div className="flex items-center gap-1">
            <button
              className="flex h-8 w-8 items-center justify-center rounded-lg text-silver/40 transition-colors hover:bg-slate-custom/30 hover:text-silver"
              aria-label="Attach file"
            >
              <Paperclip size={15} />
            </button>
            {speechSupported && (
              <button
                onClick={toggleVoice}
                disabled={isLoading}
                aria-label={isListening ? "Stop voice input" : "Start voice input"}
                aria-pressed={isListening}
                className={`flex h-8 w-8 items-center justify-center rounded-lg transition-colors ${
                  isListening
                    ? "bg-error/15 text-error animate-pulse"
                    : "text-silver/40 hover:bg-slate-custom/30 hover:text-silver"
                } disabled:opacity-30`}
                title={isListening ? "Stop listening" : "Start voice input"}
              >
                {isListening ? <MicOff size={15} /> : <Mic size={15} />}
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden sm:flex items-center gap-1.5 text-[11px] text-silver/30">
              <CornerDownLeft size={11} />
              to submit
            </span>
            <button
              onClick={handleSubmit}
              disabled={!query.trim() || isLoading}
              aria-label="Send search query"
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold/90 text-charcoal transition-all hover:bg-gold disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
