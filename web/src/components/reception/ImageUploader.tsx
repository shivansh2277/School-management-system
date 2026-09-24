import React, { useRef, useState } from "react";
import { api, API_BASE_URL, toMediaUrl } from "../../api/client";

interface ImageUploaderProps {
  value?: string | null;
  onChange: (url: string) => void;
  label?: string;
  description?: string;
  endpoint?: string;
}

export function ImageUploader({
  value,
  onChange,
  label = "Upload Image",
  description,
  endpoint = "/admin/reception/upload",
}: ImageUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showManualInput, setShowManualInput] = useState(false);

  const apiBase = API_BASE_URL;
  const displayUrl = toMediaUrl(value);

  const handleFile = async (file: File) => {
    setError(null);

    // Validate type
    const validTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|webp)$/i)) {
      setError("Please select a valid image file (.jpg, .png, .webp).");
      return;
    }

    // Validate size: 5MB
    if (file.size > 5 * 1024 * 1024) {
      setError("Image file size exceeds 5MB. Please choose a smaller image.");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await api.upload<{ url: string; filename: string; size: number }>(
        endpoint,
        formData,
      );
      if (res?.url) {
        onChange(res.url);
      } else {
        throw new Error("No URL returned from server.");
      }
    } catch (err: any) {
      setError(err?.message || "Failed to upload image. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div className="space-y-2">
      {label && <label className="block text-xs font-semibold text-ink uppercase tracking-wide">{label}</label>}

      {/* When image exists */}
      {value && displayUrl ? (
        <div className="relative border border-rule rounded-lg p-3 bg-ground/50 flex items-center gap-3">
          <div className="w-16 h-16 rounded border border-rule bg-surface overflow-hidden flex items-center justify-center shrink-0">
            <img
              src={displayUrl}
              alt="Uploaded Preview"
              className="w-full h-full object-cover"
              onError={(e) => {
                // If relative or broken URL, fallback gracefully
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          </div>

          <div className="flex-1 min-w-0">
            <span className="text-xs font-semibold text-ink block truncate">{value.split("/").pop() || "Image"}</span>
            <span className="text-[11px] text-ink-faint block truncate">{value}</span>
            <div className="mt-1 flex items-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="text-[11px] text-primary hover:underline font-medium"
              >
                Change Photo
              </button>
            </div>
          </div>

          {/* Standard Red-X Clear Button */}
          <button
            type="button"
            onClick={() => onChange("")}
            title="Remove photo"
            className="p-1 rounded text-red-500 hover:bg-red-50 transition"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ) : (
        /* Empty Upload Dropzone */
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition flex flex-col items-center justify-center gap-1.5 ${
            isDragging
              ? "border-primary bg-primary/5"
              : "border-rule hover:border-ink-faint hover:bg-ground/50"
          }`}
        >
          <div className="w-9 h-9 rounded-full bg-ground flex items-center justify-center text-ink-faint">
            {uploading ? (
              <svg className="animate-spin w-5 h-5 text-primary" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            )}
          </div>

          <p className="text-xs font-semibold text-ink">
            {uploading ? "Uploading photo..." : "Click or drag & drop to upload photo"}
          </p>
          <p className="text-[11px] text-ink-faint">PNG, JPG, or WEBP up to 5MB</p>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={onFileChange}
        className="hidden"
      />

      {error && <p className="text-xs text-red-600 font-medium">{error}</p>}
      {description && <p className="text-[11px] text-ink-faint">{description}</p>}

      {/* Direct URL Fallback Toggle */}
      <div className="pt-1">
        <button
          type="button"
          onClick={() => setShowManualInput(!showManualInput)}
          className="text-[11px] text-ink-faint hover:text-ink transition underline"
        >
          {showManualInput ? "Hide manual URL input" : "Or enter photo URL directly"}
        </button>

        {showManualInput && (
          <div className="mt-1.5">
            <input
              type="text"
              placeholder="https://... or /documents/..."
              value={value || ""}
              onChange={(e) => onChange(e.target.value)}
              className="w-full text-xs px-2.5 py-1.5 rounded border border-rule bg-surface text-ink focus:border-primary focus:outline-none"
            />
          </div>
        )}
      </div>
    </div>
  );
}
