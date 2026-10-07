import { useRef } from "react";
import { CheckCircle2, Loader2, UploadCloud, XCircle } from "lucide-react";
import { useDocuments, useUploadDocument } from "../api/queries";
import { formatDate } from "../utils/formatters";
import clsx from "clsx";

const STATUS_ICON: Record<string, JSX.Element> = {
  completed: <CheckCircle2 className="h-4 w-4 text-emerald-500" />,
  processing: <Loader2 className="h-4 w-4 animate-spin text-amber-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
};

export function DocumentPanel() {
  const { data: documents } = useDocuments();
  const upload = useUploadDocument();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File | undefined) => {
    if (file) upload.mutate(file);
  };

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <h3 className="text-sm font-semibold text-slate-600 dark:text-slate-300">Knowledge base</h3>

      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFile(e.dataTransfer.files[0]);
        }}
        className={clsx(
          "flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed p-6 text-center text-xs text-slate-400 transition hover:border-indigo-400 hover:text-indigo-500",
          upload.isPending ? "border-indigo-400" : "border-slate-300 dark:border-slate-700"
        )}
      >
        {upload.isPending ? <Loader2 className="h-6 w-6 animate-spin" /> : <UploadCloud className="h-6 w-6" />}
        <span>{upload.isPending ? "Ingesting…" : "Drop a PDF / DOCX / TXT, or click to upload"}</span>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto">
        {(documents ?? []).map((doc) => (
          <div key={doc.id} className="rounded-lg border border-slate-200 bg-white p-2.5 text-xs shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-2">
              <span className="truncate font-medium">{doc.filename}</span>
              {STATUS_ICON[doc.status] ?? null}
            </div>
            <p className="text-slate-400">
              {doc.chunks_indexed} chunks · {formatDate(doc.created_at)}
            </p>
          </div>
        ))}
        {documents?.length === 0 && <p className="text-xs text-slate-400">No documents ingested yet.</p>}
      </div>
    </div>
  );
}
