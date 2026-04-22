"use client";

import { useEffect, useState, useCallback } from "react";

const POLL_MS = 30_000;

export function StatusBar() {
  const [connected, setConnected] = useState(false);
  const [lastSync, setLastSync] = useState<Date | null>(null);
  const [secondsAgo, setSecondsAgo] = useState<number | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/health", {
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) {
        setConnected(true);
        setLastSync(new Date());
      } else {
        setConnected(false);
      }
    } catch {
      setConnected(false);
    }
  }, []);

  // Poll the health endpoint
  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, POLL_MS);
    return () => clearInterval(id);
  }, [checkHealth]);

  // Update "seconds ago" display every second
  useEffect(() => {
    const id = setInterval(() => {
      if (lastSync) {
        setSecondsAgo(Math.round((Date.now() - lastSync.getTime()) / 1000));
      }
    }, 1000);
    return () => clearInterval(id);
  }, [lastSync]);

  return (
    <div className="fixed bottom-0 left-0 right-0 h-7 bg-slate-800 border-t border-slate-700 flex items-center px-4 text-[11px] text-slate-500 z-50">
      {/* Left */}
      <span>WIN Fertility Growth Engine v0.1.0</span>

      {/* Center */}
      <div className="flex-1 flex justify-center items-center gap-1.5">
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            connected ? "bg-emerald-500" : "bg-red-500"
          }`}
        />
        <span>{connected ? "API connected" : "API disconnected"}</span>
      </div>

      {/* Right */}
      <span>
        {secondsAgo !== null
          ? `Last sync: ${secondsAgo}s ago`
          : "Last sync: --"}
      </span>
    </div>
  );
}
