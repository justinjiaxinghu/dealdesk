"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { reportService } from "@/services/report.service";
import type { ReportTemplate, ReportJob } from "@/interfaces/api";

export default function ReportsPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [jobs, setJobs] = useState<ReportJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [t, j] = await Promise.all([
        reportService.listTemplates(),
        reportService.listJobs(),
      ]);
      setTemplates(t);
      setJobs(j);
    } catch (err) {
      console.error("Failed to load reports data", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await reportService.uploadTemplate(file);
      await load();
    } catch (err) {
      console.error("Template upload failed", err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const formatBadge = (format: string) => {
    const upper = format.toUpperCase();
    return (
      <Badge variant={upper === "XLSX" ? "secondary" : "outline"}>
        {upper}
      </Badge>
    );
  };

  const statusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="default">Completed</Badge>;
      case "generating":
        return <Badge variant="secondary">Generating</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="text-muted-foreground py-12 text-center">
        Loading reports...
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Templates Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Report Templates</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Upload Excel or PowerPoint templates with fillable regions.
            </p>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.pptx"
              className="hidden"
              onChange={handleUpload}
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? "Uploading..." : "Upload Template"}
            </Button>
          </div>
        </div>

        {templates.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">
              No templates uploaded yet. Upload an XLSX or PPTX file to get
              started.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Regions</TableHead>
                <TableHead>Created</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {templates.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.name}</TableCell>
                  <TableCell>{formatBadge(t.file_format)}</TableCell>
                  <TableCell>{t.regions.length}</TableCell>
                  <TableCell>
                    {new Date(t.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => router.push(`/reports/${t.id}/fill`)}
                    >
                      Fill Report
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>

      {/* Generated Reports Section */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-bold">Generated Reports</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Reports that have been filled and generated.
          </p>
        </div>

        {jobs.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">
              No reports generated yet. Fill a template to create one.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((j) => (
                <TableRow key={j.id}>
                  <TableCell className="font-medium">{j.name}</TableCell>
                  <TableCell>{statusBadge(j.status)}</TableCell>
                  <TableCell>
                    {new Date(j.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {j.status === "completed" && (
                      <a
                        href={reportService.downloadUrl(j.id)}
                        className="text-sm text-primary underline underline-offset-4 hover:text-primary/80"
                      >
                        Download
                      </a>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>
    </div>
  );
}
