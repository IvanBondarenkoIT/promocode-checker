import {
  FormEvent,
  KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { checkHealth, checkPromocode, redeemPromocode, sendHeartbeat } from "./api";
import { playErrorBuzz, playSuccessBeep } from "./audio";
import {
  DEBOUNCE_LOCK_MS,
  digitsOnly,
  isCompleteCode,
  isSuccessResult,
  resultLabel,
  resultToTone,
} from "./logic";
import { heartbeatIntervalMs, resolvePointId } from "./pointId";
import type { CashierCodeResponse } from "./types";

export function CashierApp() {
  const inputRef = useRef<HTMLInputElement>(null);
  const lockTimerRef = useRef<number | null>(null);
  const [pointId] = useState(() => resolvePointId());
  const [code, setCode] = useState("");
  const [locked, setLocked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [lastResponse, setLastResponse] = useState<CashierCodeResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [systemReady, setSystemReady] = useState(false);

  const focusInput = useCallback(() => {
    window.setTimeout(() => {
      inputRef.current?.focus({ preventScroll: true });
      inputRef.current?.select();
    }, 0);
  }, []);

  const startLock = useCallback(() => {
    setLocked(true);
    if (lockTimerRef.current !== null) {
      window.clearTimeout(lockTimerRef.current);
    }
    lockTimerRef.current = window.setTimeout(() => {
      setLocked(false);
      lockTimerRef.current = null;
      focusInput();
    }, DEBOUNCE_LOCK_MS);
  }, [focusInput]);

  useEffect(() => {
    focusInput();
    const recover = (event: Event) => {
      const target = event.target;
      if (target instanceof HTMLElement && target.closest("button")) {
        return;
      }
      focusInput();
    };
    window.addEventListener("pointerdown", recover);
    window.addEventListener("focus", recover);
    document.addEventListener("visibilitychange", recover);
    return () => {
      window.removeEventListener("pointerdown", recover);
      window.removeEventListener("focus", recover);
      document.removeEventListener("visibilitychange", recover);
      if (lockTimerRef.current !== null) {
        window.clearTimeout(lockTimerRef.current);
      }
    };
  }, [focusInput]);

  useEffect(() => {
    let cancelled = false;

    const beat = async () => {
      const healthy = await checkHealth();
      if (cancelled) {
        return;
      }
      if (!healthy) {
        setSystemReady(false);
        return;
      }
      try {
        await sendHeartbeat(pointId);
        if (!cancelled) {
          setSystemReady(true);
        }
      } catch {
        if (!cancelled) {
          setSystemReady(false);
        }
      }
    };

    void beat();
    const id = window.setInterval(() => {
      void beat();
    }, heartbeatIntervalMs());

    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [pointId]);

  const applyResponse = useCallback((response: CashierCodeResponse) => {
    setLastResponse(response);
    setErrorMessage(null);
    if (isSuccessResult(response.result)) {
      playSuccessBeep();
    } else {
      playErrorBuzz();
    }
  }, []);

  const runCheck = useCallback(
    async (rawCode: string) => {
      if (locked || busy) {
        return;
      }
      const normalized = digitsOnly(rawCode);
      if (!isCompleteCode(normalized)) {
        return;
      }
      setBusy(true);
      setErrorMessage(null);
      try {
        const response = await checkPromocode(normalized, pointId);
        applyResponse(response);
        setSystemReady(true);
      } catch (error) {
        setLastResponse(null);
        setErrorMessage(error instanceof Error ? error.message : "Check failed");
        playErrorBuzz();
      } finally {
        setBusy(false);
        startLock();
        setCode("");
        focusInput();
      }
    },
    [applyResponse, busy, focusInput, locked, pointId, startLock],
  );

  const runRedeem = useCallback(async () => {
    if (busy || !lastResponse || lastResponse.result !== "valid") {
      return;
    }
    setBusy(true);
    setErrorMessage(null);
    try {
      const response = await redeemPromocode(lastResponse.code, pointId);
      applyResponse(response);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Redeem failed");
      playErrorBuzz();
    } finally {
      setBusy(false);
      startLock();
      setCode("");
      focusInput();
    }
  }, [applyResponse, busy, focusInput, lastResponse, pointId, startLock]);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void runCheck(code);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      void runCheck(code);
    }
  };

  const onChange = (value: string) => {
    if (locked || busy) {
      return;
    }
    const next = digitsOnly(value);
    setCode(next);
    if (isCompleteCode(next)) {
      void runCheck(next);
    }
  };

  const tone = errorMessage ? "error" : resultToTone(lastResponse?.result ?? null);
  const statusText = errorMessage ? "ERROR" : resultLabel(lastResponse?.result ?? null);
  const canRedeem = !busy && lastResponse?.result === "valid";

  return (
    <div className="cashier-shell" data-testid="cashier-shell">
      <header className="cashier-topbar">
        <div className="shop-badge">
          <div className="meta-label">Shop</div>
          <div className="meta-value" data-testid="point-id">
            {pointId}
          </div>
        </div>
        <div
          className={`ready-indicator ${systemReady ? "ready-indicator--ok" : "ready-indicator--off"}`}
          data-testid="system-ready"
          aria-live="polite"
        >
          <span className="ready-lamp" aria-hidden="true" />
          <span>{systemReady ? "Ready" : "Connecting…"}</span>
        </div>
      </header>

      <main className="cashier-main">
        <p className="brand">Promocode Checker</p>

        <div
          className={`status-panel tone-${tone}`}
          data-testid="status-panel"
          role="status"
          aria-live="polite"
        >
          <div className="status-label">{statusText}</div>
          <div className="status-code">{lastResponse?.code || code || "—"}</div>
          {errorMessage ? <div className="status-detail">{errorMessage}</div> : null}
        </div>

        <form className="scan-form" onSubmit={onSubmit}>
          <label className="sr-only" htmlFor="promocode-input">
            Promocode
          </label>
          <input
            id="promocode-input"
            ref={inputRef}
            className="scan-input"
            data-testid="promocode-input"
            inputMode="numeric"
            autoComplete="off"
            autoCorrect="off"
            spellCheck={false}
            maxLength={8}
            value={code}
            disabled={locked || busy}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={onKeyDown}
            onBlur={focusInput}
            placeholder="••••••••"
          />
        </form>

        <button
          type="button"
          className={`redeem-button ${canRedeem ? "redeem-button--ready" : ""}`}
          data-testid="redeem-button"
          disabled={!canRedeem}
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => void runRedeem()}
        >
          Apply discount
        </button>

        {(locked || busy) && (
          <p className="lock-hint" data-testid="lock-hint">
            {busy ? "Processing…" : "Pause 1.5s"}
          </p>
        )}
      </main>
    </div>
  );
}
