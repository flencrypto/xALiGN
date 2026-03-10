'use client';

import { useEffect, useRef, useState } from 'react';
import Header from '@/components/layout/Header';
import { uploadsApi, UploadedPhoto } from '@/lib/api';

export default function PhotosPage() {
  const [photos, setPhotos] = useState<UploadedPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [altText, setAltText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchPhotos = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await uploadsApi.list();
      setPhotos(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load photos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPhotos();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadsApi.uploadPhoto(file, { alt_text: altText || undefined });
      setAltText('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      fetchPhotos();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this photo?')) return;
    try {
      await uploadsApi.delete(id);
      fetchPhotos();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Delete failed');
    }
  };

  const formatBytes = (bytes?: number) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex flex-col min-h-full">
      <Header title="Photos & Uploads" />

      <div className="flex-1 p-6 space-y-6">
        <p className="text-sm text-muted-foreground">Manage uploaded photos and files</p>

        {/* Upload panel */}
        <div className="glass-card p-4 space-y-3">
          <h2 className="text-sm font-semibold text-color-text-main uppercase tracking-wider font-mono">
            Upload New Photo
          </h2>
          <div className="flex flex-wrap gap-3 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="label">Alt Text</label>
              <input
                className="input w-full"
                placeholder="Describe the image…"
                value={altText}
                onChange={(e) => setAltText(e.target.value)}
                disabled={uploading}
              />
            </div>
            <div>
              <label className="label">File</label>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="block text-sm text-color-text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-mono file:bg-color-primary/20 file:text-color-primary hover:file:bg-color-primary/30 cursor-pointer"
                onChange={handleUpload}
                disabled={uploading}
              />
            </div>
          </div>
          {uploading && (
            <p className="text-xs text-color-text-muted font-mono animate-pulse">Uploading…</p>
          )}
          {uploadError && (
            <p className="text-xs text-red-400">{uploadError}</p>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="glass-card p-4 border border-red-500/30 text-red-400">{error}</div>
        )}

        {/* Grid */}
        {loading ? (
          <div className="p-8 text-center text-color-text-muted font-mono animate-pulse">
            Loading photos…
          </div>
        ) : photos.length === 0 ? (
          <div className="glass-card p-8 text-center text-color-text-muted">
            No photos uploaded yet. Use the upload panel above to get started.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {photos.map((photo) => (
              <div key={photo.id} className="glass-card overflow-hidden flex flex-col">
                {/* Preview */}
                <div className="relative bg-color-border-subtle/10 aspect-video flex items-center justify-center overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={uploadsApi.fileUrl(photo.id)}
                    alt={photo.alt_text ?? photo.original_filename}
                    className="object-cover w-full h-full"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>

                {/* Metadata */}
                <div className="p-3 flex-1 space-y-1.5">
                  <p className="text-sm font-medium text-color-text-main truncate" title={photo.original_filename}>
                    {photo.original_filename}
                  </p>
                  {photo.alt_text && (
                    <p className="text-xs text-color-text-muted truncate" title={photo.alt_text}>
                      {photo.alt_text}
                    </p>
                  )}
                  {photo.ai_description && (
                    <p className="text-xs text-color-text-faint line-clamp-2" title={photo.ai_description}>
                      {photo.ai_description}
                    </p>
                  )}
                  <div className="flex items-center justify-between text-[10px] font-mono text-color-text-faint pt-1">
                    <span>{formatBytes(photo.size_bytes)}</span>
                    <span>{photo.uploaded_at ? new Date(photo.uploaded_at).toLocaleDateString() : '—'}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="px-3 pb-3 flex gap-2">
                  <a
                    href={uploadsApi.fileUrl(photo.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-color-primary hover:underline"
                  >
                    View
                  </a>
                  <button
                    className="text-xs text-red-400 hover:text-red-300 ml-auto"
                    onClick={() => handleDelete(photo.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
