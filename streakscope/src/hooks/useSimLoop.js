import { useState, useCallback, useRef } from "react";
import {
  DEFAULT_SIM_CONFIG,
  runSimLoop,
  formatSimMarkdown,
  downloadMarkdown,
} from "../lib/simTrader.js";

export function useSimLoop({ traders, ignoreFavorites }) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [markdown, setMarkdown] = useState("");
  const [config, setConfig] = useState({ ...DEFAULT_SIM_CONFIG });
  const abortRef = useRef(false);

  const run = useCallback(() => {
    if (!traders.length || running) return;
    abortRef.current = false;
    setRunning(true);
    setResult(null);
    setMarkdown("");

    requestAnimationFrame(() => {
      if (abortRef.current) {
        setRunning(false);
        return;
      }
      const out = runSimLoop(traders, config, ignoreFavorites);
      const md = formatSimMarkdown(out, config);
      setResult(out);
      setMarkdown(md);
      setRunning(false);
    });
  }, [traders, config, ignoreFavorites, running]);

  const exportLog = useCallback(() => {
    if (markdown) downloadMarkdown(markdown);
  }, [markdown]);

  const updateConfig = useCallback((patch) => {
    setConfig((prev) => ({ ...prev, ...patch }));
  }, []);

  return {
    running,
    result,
    markdown,
    config,
    updateConfig,
    run,
    exportLog,
  };
}
