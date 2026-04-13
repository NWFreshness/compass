"use client";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export function Header({ title }: { title?: string }) {
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }
    const stored = window.localStorage.getItem("theme");
    return stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches);
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    window.localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  function toggleTheme() {
    setDark((current) => !current);
  }

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b bg-white dark:bg-slate-900">
      <h1 className="text-base font-semibold text-slate-800 dark:text-slate-100">{title}</h1>
      <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
        {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>
    </header>
  );
}
