async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    if (res.status === 401) throw Object.assign(new Error("UNAUTHORIZED"), { status: 401 });
    if (res.status === 403) throw Object.assign(new Error("FORBIDDEN"), { status: 403 });
    const err = await res.json().catch(() => ({}));
    throw Object.assign(new Error(err.detail ?? `HTTP ${res.status}`), { status: res.status });
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function postStream(
  path: string,
  onToken: (token: string) => void,
  onDone: (recId: string) => void,
  onError: (msg: string) => void,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { method: "POST", credentials: "include" });
  } catch {
    onError("Network error");
    return;
  }
  if (!res.ok || !res.body) {
    onError(`HTTP ${res.status}`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let settled = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload: unknown = JSON.parse(line.slice(6));
      if (typeof payload !== "string") continue;
      if (payload.startsWith("\n__DONE__:")) {
        settled = true;
        onDone(payload.slice("\n__DONE__:".length));
      } else if (payload.startsWith("\n__ERROR__:")) {
        settled = true;
        onError(payload.slice("\n__ERROR__:".length));
      } else {
        onToken(payload);
      }
    }
  }

  if (!settled) {
    onError("Stream ended unexpectedly");
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData, headers: {} }),
  postStream,
};
