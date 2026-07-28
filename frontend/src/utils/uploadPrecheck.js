// Builds a lightweight copy of an upload FormData for the precheck request:
// every "fastq_files" entry is replaced with a 1-byte placeholder that keeps
// the original filename (needed for metadata/filename matching on the server)
// but drops the actual file content, so the precheck request stays tiny even
// for multi-GB submissions. Metadata/antibiotics files are kept as-is since
// their content is what gets validated.
export function toPrecheckFormData(fd) {
  const precheckFd = new FormData();
  for (const [key, value] of fd.entries()) {
    if (key === "fastq_files" && value instanceof File) {
      precheckFd.append(key, new File(["x"], value.name, { type: value.type }));
    } else {
      precheckFd.append(key, value);
    }
  }
  return precheckFd;
}

// Pulls a human-readable message out of a failed upload/precheck request.
// Normally the backend returns JSON ({ error } or { errors }), but on a crash
// severe enough to bypass our own view (e.g. a killed worker), the response
// body can be a raw HTML error page instead - show a clean fallback rather
// than dumping that markup as text.
export function extractErrorMessage(err) {
  const data = err?.response?.data;
  if (data && typeof data === "object") {
    if (data.error) return data.error;
    if (data.errors) return JSON.stringify(data.errors, null, 2);
  }
  if (typeof data === "string" && data.trim().startsWith("<")) {
    const status = err?.response?.status || "unknown";
    return `The server ran into an unexpected error (HTTP ${status}) and didn't return a normal response. Please try again, or contact support if this keeps happening.`;
  }
  return data || err.message;
}
