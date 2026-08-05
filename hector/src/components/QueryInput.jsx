"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Paperclip,
  CornerDownLeft,
  Mic,
  MicOff,
  X,
  FileText,
  FileImage,
  File,
  FileCode,
  ExternalLink,
} from "lucide-react";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(type, name) {
  if (type?.startsWith("image/")) return FileImage;
  if (type?.includes("pdf")) return FileText;
  if (
    type?.includes("text") ||
    type?.includes("json") ||
    type?.includes("javascript") ||
    type?.includes("python") ||
    name?.match(/\.(py|js|jsx|ts|tsx|json|txt|md|csv|log)$/i)
  )
    return FileCode;
  return File;
}

function getFileColor(type) {
  if (type?.startsWith("image/")) return "text-blue-400";
  if (type?.includes("pdf")) return "text-red-400";
  if (type?.includes("text") || type?.includes("json")) return "text-green-400";
  return "text-silver/50";
}

function FilePreviewModal({ file, previewUrl, textPreview, onClose }) {
  const Icon = getFileIcon(file.type, file.name);
  const isImage = file.type?.startsWith("image/");

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[85vh] rounded-xl border border-slate-custom/40 bg-cream shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-custom/30 px-5 py-3">
          <div className="flex items-center gap-2 min-w-0">
            <Icon size={16} className={getFileColor(file.type)} />
            <span className="text-[13px] font-medium text-gold-light truncate">
              {file.name}
            </span>
            <span className="text-[11px] text-silver/30 shrink-0">
              {formatFileSize(file.size)}
            </span>
          </div>
          <button
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-md text-silver/40 hover:bg-slate-custom/30 hover:text-silver shrink-0"
          >
            <X size={14} />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-5">
          {isImage && previewUrl ? (
            <img
              src={previewUrl}
              alt={file.name}
              className="max-w-full max-h-[65vh] rounded-lg object-contain mx-auto"
            />
          ) : textPreview ? (
            <pre className="whitespace-pre-wrap break-words rounded-lg bg-charcoal/60 p-4 text-[12px] font-mono leading-relaxed text-silver/70 max-h-[65vh] overflow-auto">
              {textPreview}
            </pre>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Icon size={48} className={`${getFileColor(file.type)} mb-4 opacity-40`} />
              <p className="text-[13px] text-silver/50">{file.name}</p>
              <p className="text-[11px] text-silver/30 mt-1">
                {formatFileSize(file.size)} &middot; {file.type || "Unknown type"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function QueryInput({
  onSubmit,
  isLoading,
  showSuggestions,
  suggestions = [],
  resetKey = 0,
}) {
  const [query, setQuery] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [textPreview, setTextPreview] = useState(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [fileError, setFileError] = useState(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    setQuery("");
    setAttachedFile(null);
    setPreviewUrl(null);
    setTextPreview(null);
    setFileError(null);
  }, [resetKey]);

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

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

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileError(null);

    if (file.size > MAX_FILE_SIZE) {
      setFileError(`File too large (${formatFileSize(file.size)}). Max 10 MB.`);
      e.target.value = "";
      return;
    }

    setAttachedFile(file);

    // Generate preview
    if (file.type?.startsWith("image/")) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setTextPreview(null);
    } else if (
      file.type?.includes("text") ||
      file.type?.includes("json") ||
      file.type?.includes("javascript") ||
      file.type?.includes("python") ||
      file.type?.includes("csv") ||
      file.type?.includes("xml") ||
      file.type?.includes("html") ||
      file.name?.match(/\.(py|js|jsx|ts|tsx|json|txt|md|csv|log|xml|html|css|yaml|yml)$/i)
    ) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const text = ev.target?.result;
        setTextPreview(
          typeof text === "string"
            ? text.length > 3000
              ? text.slice(0, 3000) + "\n\n... (truncated)"
              : text
            : null
        );
      };
      reader.readAsText(file.slice(0, 50000)); // Read first 50KB for preview
      setPreviewUrl(null);
    } else {
      setPreviewUrl(null);
      setTextPreview(null);
    }

    // Reset input so same file can be re-selected
    e.target.value = "";
  }, []);

  const removeFile = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setAttachedFile(null);
    setPreviewUrl(null);
    setTextPreview(null);
    setFileError(null);
  }, [previewUrl]);

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSubmit(query.trim(), attachedFile);
      setQuery("");
      removeFile();
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

  const FileIcon = attachedFile
    ? getFileIcon(attachedFile.type, attachedFile.name)
    : File;

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

      {/* Attached file preview chip */}
      {attachedFile && (
        <div className="mb-2 flex items-center gap-2 animate-fade-in">
          <button
            onClick={() => setShowPreviewModal(true)}
            className="flex items-center gap-2 rounded-lg border border-slate-custom/40 bg-charcoal/60 px-3 py-2 text-left transition-colors hover:border-gold/30 hover:bg-gold/5 group max-w-full"
          >
            <FileIcon
              size={14}
              className={`${getFileColor(attachedFile.type)} shrink-0`}
            />
            <div className="min-w-0">
              <p className="text-[11px] font-medium text-silver/70 truncate max-w-[200px]">
                {attachedFile.name}
              </p>
              <p className="text-[9px] text-silver/30">
                {formatFileSize(attachedFile.size)}
              </p>
            </div>
            <ExternalLink
              size={10}
              className="text-silver/20 group-hover:text-gold/40 shrink-0"
            />
          </button>
          <button
            onClick={removeFile}
            className="flex h-6 w-6 items-center justify-center rounded-md text-silver/30 transition-colors hover:bg-error/10 hover:text-error shrink-0"
            aria-label="Remove attached file"
          >
            <X size={12} />
          </button>
        </div>
      )}

      {fileError && (
        <div className="mb-2 flex items-center gap-2 rounded-lg border border-error/20 bg-error/5 px-3 py-2 text-[11px] text-error animate-fade-in">
          {fileError}
          <button
            onClick={() => setFileError(null)}
            className="ml-auto text-silver/30 hover:text-error"
          >
            <X size={10} />
          </button>
        </div>
      )}

      <div className="relative rounded-xl border border-slate-custom/60 bg-charcoal/80 transition-all focus-within:border-gold/40 focus-within:shadow-[0_0_0_1px_rgba(201,169,98,0.1)]">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            attachedFile
              ? "Ask about this file..."
              : 'Enter your legal query - e.g., "What is the BNS equivalent of IPC Section 302?"'
          }
          rows={1}
          disabled={isLoading}
          autoComplete="off"
          aria-label="Legal search query"
          role="searchbox"
          className="w-full resize-none bg-transparent px-4 pt-4 pb-12 text-[14.5px] text-gold-light placeholder-silver/40 outline-none disabled:opacity-50"
        />

        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 py-2.5">
          <div className="flex items-center gap-1">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept="*/*"
              onChange={handleFileSelect}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-silver/40 transition-colors hover:bg-slate-custom/30 hover:text-silver disabled:opacity-30"
              aria-label="Attach file"
              title="Attach file (PDF, image, text, code)"
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

      {/* File preview modal */}
      {showPreviewModal && attachedFile && (
        <FilePreviewModal
          file={attachedFile}
          previewUrl={previewUrl}
          textPreview={textPreview}
          onClose={() => setShowPreviewModal(false)}
        />
      )}
    </div>
  );
}
