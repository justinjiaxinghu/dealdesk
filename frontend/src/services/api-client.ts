// frontend/src/services/api-client.ts
// Base fetch wrapper for the DealDesk API.

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore parse error, keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

/**
 * Generic fetch wrapper that sends JSON and returns a typed response.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  const res = await fetch(url, {
    ...options,
    headers,
  });

  return handleResponse<T>(res);
}

/**
 * Upload a file via multipart/form-data. Do NOT set Content-Type header;
 * the browser will set the correct multipart boundary automatically.
 */
export async function apiUpload<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });

  return handleResponse<T>(res);
}
