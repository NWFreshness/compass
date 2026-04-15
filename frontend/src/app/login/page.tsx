"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

function CompassMark() {
  return (
    <svg width="56" height="56" viewBox="0 0 56 56" fill="none" aria-hidden="true">
      <circle cx="28" cy="28" r="26" stroke="currentColor" strokeWidth="1.25" strokeOpacity="0.3" />
      <circle cx="28" cy="28" r="21" stroke="currentColor" strokeWidth="0.75" strokeOpacity="0.18" />
      <circle cx="28" cy="28" r="16" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.12" />
      <line x1="28" y1="2" x2="28" y2="7" stroke="currentColor" strokeWidth="2" strokeOpacity="0.5" strokeLinecap="round" />
      <line x1="28" y1="49" x2="28" y2="54" stroke="currentColor" strokeWidth="2" strokeOpacity="0.22" strokeLinecap="round" />
      <line x1="2" y1="28" x2="7" y2="28" stroke="currentColor" strokeWidth="2" strokeOpacity="0.22" strokeLinecap="round" />
      <line x1="49" y1="28" x2="54" y2="28" stroke="currentColor" strokeWidth="2" strokeOpacity="0.22" strokeLinecap="round" />
      <line x1="8.1" y1="8.1" x2="11.2" y2="11.2" stroke="currentColor" strokeWidth="1" strokeOpacity="0.15" strokeLinecap="round" />
      <line x1="44.8" y1="11.2" x2="47.9" y2="8.1" stroke="currentColor" strokeWidth="1" strokeOpacity="0.15" strokeLinecap="round" />
      <line x1="8.1" y1="47.9" x2="11.2" y2="44.8" stroke="currentColor" strokeWidth="1" strokeOpacity="0.15" strokeLinecap="round" />
      <line x1="44.8" y1="44.8" x2="47.9" y2="47.9" stroke="currentColor" strokeWidth="1" strokeOpacity="0.15" strokeLinecap="round" />
      <path d="M28 7L31.5 22H24.5L28 7Z" fill="var(--cp-amber)" />
      <path d="M28 49L24.5 34H31.5L28 49Z" fill="currentColor" opacity="0.25" />
      <path d="M49 28L34 24.5V31.5L49 28Z" fill="currentColor" opacity="0.15" />
      <path d="M7 28L22 31.5V24.5L7 28Z" fill="currentColor" opacity="0.15" />
      <circle cx="28" cy="28" r="3.5" fill="var(--cp-amber)" opacity="0.9" />
      <circle cx="28" cy="28" r="1.5" fill="currentColor" opacity="0.85" />
    </svg>
  );
}

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { refresh } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/login", { username, password });
      await refresh();
      router.push("/students");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-background">
      {/* Dot-grid background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: "radial-gradient(circle, var(--cp-amber) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          opacity: 0.12,
        }}
      />
      {/* Radial vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 75% 75% at 50% 50%, transparent 30%, var(--background) 100%)",
        }}
      />

      <div
        className="relative z-10 w-full max-w-[360px] px-5"
        style={{ animation: "fade-up 0.45s ease-out both" }}
      >
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-5 text-muted-foreground">
            <CompassMark />
          </div>
          <h1
            className="font-semibold tracking-wide leading-none text-foreground"
            style={{ fontFamily: "var(--font-heading)", fontSize: "2.5rem" }}
          >
            Compass
          </h1>
          <p
            className="uppercase font-sans mt-2 text-muted-foreground"
            style={{ fontSize: "0.65rem", letterSpacing: "0.25em" }}
          >
            Student Analytics &amp; MTSS
          </p>
        </div>

        {/* Form card */}
        <div
          className="rounded-xl px-6 py-6 space-y-5 bg-card ring-1 ring-foreground/10"
          style={{ boxShadow: "0 4px 24px var(--border)" }}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label
                htmlFor="username"
                className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground"
              >
                Username
              </Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                className="h-10 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label
                htmlFor="password"
                className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground"
              >
                Password
              </Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                className="h-10 text-sm"
              />
            </div>

            {error && (
              <p className="text-xs px-3 py-2 rounded-md text-destructive bg-destructive/10 border border-destructive/20">
                {error}
              </p>
            )}

            <Button
              type="submit"
              className="w-full h-10 font-medium tracking-wide text-sm mt-1"
              disabled={loading}
            >
              {loading ? "Signing in\u2026" : "Sign in"}
            </Button>
          </form>
        </div>

        <p
          className="text-center mt-5 text-[10px] uppercase tracking-widest text-muted-foreground/50"
        >
          Multi-Tiered System of Supports
        </p>
      </div>
    </div>
  );
}
