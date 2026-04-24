"use client";

import { useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Upload, ArrowLeft, CheckCircle2, XCircle, AlertCircle, FileText, Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";
import { apiFetch, ApiError, API_BASE } from "@/lib/api/client";
import { useAuthToken } from "@/hooks/queries/use-auth-token";
import { useMyOrganization } from "@/hooks/queries/use-organizations";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { buildLoginNextPath } from "../../auth-recovery";

// ── Types ──────────────────────────────────────────────────────────────────────

interface InviteRowResult {
  row: number;
  email: string;
  status: "created" | "duplicate" | "error";
  error: string | null;
}

interface BulkInviteResponse {
  batch_id: string;
  total: number;
  created: number;
  duplicates: number;
  errors: number;
  results: InviteRowResult[];
}

// ── Status indicator ───────────────────────────────────────────────────────────

function StatusIcon({ status }: { status: InviteRowResult["status"] }) {
  if (status === "created") return <CheckCircle2 className="size-4 text-green-400 shrink-0" />;
  if (status === "duplicate") return <AlertCircle className="size-4 text-amber-400 shrink-0" />;
  return <XCircle className="size-4 text-purple-400 shrink-0" />;
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function BulkInvitePage() {
  const { locale } = useParams<{ locale: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const getToken = useAuthToken();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const reauthPath = buildLoginNextPath(locale, `/${locale}/my-organization/invite`);

  const { data: org, isLoading: orgLoading, error: orgError, refetch: refetchOrg } = useMyOrganization();
  const { energy } = useEnergyMode();
  const isLow = energy === "low";
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<BulkInviteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setResult(null);
    setError(null);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f && f.name.endsWith(".csv")) {
      setFile(f);
      setResult(null);
      setError(null);
    }
  }

  async function handleUpload() {
    if (!file || !org) return;
    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_BASE}/organizations/${org.id}/invites/bulk`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        },
      );

      const json = await response.json();
      if (!response.ok) {
        const err = json.error ?? json.detail ?? { message: response.statusText };
        throw new Error(err.message ?? "Upload failed");
      }

      // Unwrap envelope if present
      const data: BulkInviteResponse = json.data !== undefined ? json.data : json;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error.generic"));
    } finally {
      setUploading(false);
    }
  }

  if (orgLoading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-8 space-y-6" role="status" aria-live="polite">
        <Skeleton className="h-5 w-16" />
        <div className="space-y-2">
          <Skeleton className="h-7 w-56" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-20 w-full rounded-xl" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    );
  }

  if (orgError instanceof ApiError && orgError.status === 401) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center space-y-4">
        <p className="text-sm font-medium text-foreground">
          {t("orgs.authExpiredTitle", { defaultValue: "Session expired" })}
        </p>
        <p className="text-sm text-muted-foreground">
          {t("orgs.authExpiredDesc", { defaultValue: "Please sign in again to manage organization invites." })}
        </p>
        <Button onClick={() => router.replace(reauthPath)}>
          {t("orgs.signInAgain", { defaultValue: "Sign in again" })}
        </Button>
      </div>
    );
  }

  if (orgError) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center space-y-4">
        <p className="text-sm font-medium text-foreground">
          {t("orgs.loadErrorTitle", { defaultValue: "Something went wrong" })}
        </p>
        <p className="text-sm text-muted-foreground">
          {t("orgs.loadErrorDesc", { defaultValue: "Could not load your organization. Please try again." })}
        </p>
        <Button variant="outline" onClick={() => void refetchOrg()}>
          {t("common.retry", { defaultValue: "Retry" })}
        </Button>
      </div>
    );
  }

  if (!org) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-muted-foreground">
          {t("orgs.noOrganization", { defaultValue: "You don't have an organization yet." })}
        </p>
        <Button
          className="mt-4"
          onClick={() => router.push(`/${locale}/my-organization`)}
        >
          {t("orgs.createOrg", { defaultValue: "Create Organization" })}
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
      {/* Back */}
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 text-muted-foreground"
        onClick={() => router.push(`/${locale}/my-organization`)}
      >
        <ArrowLeft className="size-4 mr-1" />
        {t("common.back", { defaultValue: "Back" })}
      </Button>

      {/* Header */}
      <div>
        <h1 className="text-xl font-bold">{t("orgs.bulkInvite", { defaultValue: "Bulk Invite Professionals" })}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {t("orgs.bulkInviteDesc", { defaultValue: "Upload a CSV with email addresses to invite professionals to Volaura." })}
        </p>
      </div>

      {/* CSV format info — hidden at low energy */}
      {!isLow && (
        <div className="rounded-xl border border-border bg-card p-4 text-sm space-y-1">
          <p className="font-medium flex items-center gap-2">
            <FileText className="size-4 text-muted-foreground" />
            {t("orgs.csvFormat", { defaultValue: "CSV format" })}
          </p>
          <p className="text-xs text-muted-foreground font-mono">
            email,display_name,phone,skills
          </p>
          <p className="text-xs text-muted-foreground">
            {t("orgs.csvFormatDesc", { defaultValue: "Only email is required. Max 500 rows, 1 MB." })}
          </p>
        </div>
      )}

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors",
          file
            ? "border-primary/50 bg-primary/5"
            : "border-border hover:border-primary/30 hover:bg-muted/20",
        )}
        role="button"
        tabIndex={0}
        aria-label={t("orgs.dropCSV", { defaultValue: "Click or drop CSV file here" })}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInputRef.current?.click(); } }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={handleFileChange}
          className="hidden"
          aria-hidden="true"
        />
        {file ? (
          <div className="flex flex-col items-center gap-2">
            <CheckCircle2 className="size-8 text-green-400" />
            <p className="text-sm font-medium">{file.name}</p>
            <p className="text-xs text-muted-foreground">
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-muted-foreground">
            <Upload className="size-8" />
            <p className="text-sm">{t("orgs.dropCSV", { defaultValue: "Click or drop CSV file here" })}</p>
          </div>
        )}
      </div>

      {/* Upload button */}
      {file && !result && (
        <Button
          onClick={handleUpload}
          disabled={uploading}
          className="w-full gap-2"
          size="lg"
        >
          {uploading ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              {t("loading.uploading", { defaultValue: "Uploading..." })}
            </>
          ) : (
            <>
              <Upload className="size-4" />
              {t("orgs.uploadInvites", { defaultValue: "Upload Invites" })}
            </>
          )}
        </Button>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 flex items-start gap-3">
          <XCircle className="size-5 text-destructive shrink-0 mt-0.5" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-3 text-center">
              <p className="text-2xl font-bold tabular-nums text-green-400">{result.created}</p>
              <p className="text-xs text-muted-foreground">{t("orgs.inviteCreated", { defaultValue: "Created" })}</p>
            </div>
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-center">
              <p className="text-2xl font-bold tabular-nums text-amber-400">{result.duplicates}</p>
              <p className="text-xs text-muted-foreground">{t("orgs.inviteDuplicate", { defaultValue: "Skipped" })}</p>
            </div>
            <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-3 text-center">
              <p className="text-2xl font-bold tabular-nums text-purple-400">{result.errors}</p>
              <p className="text-xs text-muted-foreground">{t("orgs.inviteError", { defaultValue: "Errors" })}</p>
            </div>
          </div>

          {/* Row details — hidden at low energy */}
          {!isLow && (
            <div className="rounded-xl border border-border bg-card divide-y divide-border overflow-hidden">
              {result.results.map((row) => (
                <div key={`${row.row}-${row.email}`} className="flex items-center gap-3 px-4 py-2.5">
                  <StatusIcon status={row.status} />
                  <span className="flex-1 text-sm truncate">{row.email}</span>
                  {row.error && (
                    <span className="text-xs text-destructive shrink-0">{row.error}</span>
                  )}
                  <span className={cn(
                    "text-xs font-medium shrink-0",
                    row.status === "created" ? "text-green-400" :
                    row.status === "duplicate" ? "text-amber-400" : "text-purple-400"
                  )}>
                    {row.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Upload another */}
          <Button
            variant="outline"
            className="w-full"
            onClick={() => { setFile(null); setResult(null); setError(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}
          >
            {t("orgs.uploadAnother", { defaultValue: "Upload Another File" })}
          </Button>
        </motion.div>
      )}
    </div>
  );
}
