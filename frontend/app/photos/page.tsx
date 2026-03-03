'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/layout/Header';
import { uploadsApi, UploadedPhoto } from '@/lib/api';

export default function PhotosPage() {
  const [photos, setPhotos] = useState<UploadedPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [altText, setAltText] = useState('');
  const [companyIntelId, setCompanyIntelId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    uploadsApi.list().then(setPhotos).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadError('');
    try {
      const photo = await uploadsApi.uploadPhoto(file, {
        alt_text: altText || undefined,
        company_intel_id: companyIntelId ? parseInt(companyIntelId, 10) : undefined,
      });
      setPhotos((prev) => [photo, ...prev]);
      setFile(null);
      setAltText('');
      setCompanyIntelId('');
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <Header title="Intelligence Photos" />
      <div className="p-6 space-y-6">
        {/* Upload form */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
          <h2 className="text-white font-semibold mb-4">Upload Photo</h2>
          <form onSubmit={handleUpload} className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="block text-slate-400 text-xs mb-1">Photo</label>
              <input
                required
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 file:mr-3 file:bg-blue-600 file:text-white file:border-0 file:rounded file:px-2 file:py-0.5 file:text-xs"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-xs mb-1">Alt Text (optional)</label>
              <input
                type="text"
                placeholder="e.g. Site photo"
                value={altText}
                onChange={(e) => setAltText(e.target.value)}
                className="w-40 bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-xs mb-1">Company Intel ID (optional)</label>
              <input
                type="number"
                placeholder="e.g. 1"
                value={companyIntelId}
                onChange={(e) => setCompanyIntelId(e.target.value)}
                className="w-36 bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={uploading || !file}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
            >
              {uploading ? 'Uploading…' : 'Upload'}
            </button>
          </form>
          {uploadError && <p className="text-red-400 text-sm mt-2">{uploadError}</p>}
        </div>

        {/* Gallery */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-40 bg-slate-800 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : photos.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-4xl mb-3">🖼️</p>
            <p className="text-slate-400">No photos uploaded yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {photos.map((photo) => (
              <div key={photo.id} className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
                <div className="bg-slate-700/50 h-32 flex items-center justify-center">
                  <span className="text-4xl">🖼️</span>
                </div>
                <div className="p-3">
                  <p className="text-white text-sm font-medium truncate">{photo.original_filename}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {photo.content_type && (
                      <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs border border-blue-500/30">
                        {photo.content_type}
                      </span>
                    )}
                    {photo.uploaded_at && (
                      <span className="text-slate-500 text-xs">
                        {new Date(photo.uploaded_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  {photo.ai_description && (
                    <div className="mt-2">
                      <button
                        onClick={() => setExpanded(expanded === photo.id ? null : photo.id)}
                        className="text-blue-400 hover:text-blue-300 text-xs"
                      >
                        {expanded === photo.id ? '▲ Hide AI Description' : '▼ AI Description'}
                      </button>
                      {expanded === photo.id && (
                        <p className="mt-2 text-xs text-slate-300 bg-slate-700/50 rounded p-2">
                          {photo.ai_description}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
