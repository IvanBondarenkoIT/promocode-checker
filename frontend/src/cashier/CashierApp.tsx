import {
  FormEvent,
  KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { checkPromocode, redeemPromocode, sendHeartbeat } from "./api";
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

function formatTime(value: Date | null): string {
  if (!value) {
    return "—";
  }
  return value.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function CashierApp() {
  const inputRef = useRef<HTMLInputElement>(null);
  const lockTimerRef = useRef<number | null>(null);
  const [pointId] = useState(() => resolvePointId());
  const [code, setCode] = useState("");
  const [locked, setLocked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [lastResponse, setLastResponse] = useState<CashierCodeResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sessionStartedAt] = useState(() => new Date());
  const [lastActivityAt, setLastActivityAt] = useState(() => new Date());
  const [lastHeartbeatAt, setLastHeartbeatAt] = useState<Date | null>(null);

  const focusInput = useCallback(() => {
    window.setTimeout(() => {
      inputRef.current?.focus({ preventScroll: true });
      inputRef.current?.select();
    }, 0);
  }, []);

  const markActivity = useCallback(() => {
    setLastActivityAt(new Date());
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
      try {
        await sendHeartbeat(pointId);
        if (!cancelled) {
          setLastHeartbeatAt(new Date());
        }
      } catch {
        // Heartbeat is best-effort; UI stays usable offline of heartbeat.
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

  const applyResponse = useCallback(
    (response: CashierCodeResponse) => {
      setLastResponse(response);
      setErrorMessage(null);
      markActivity();
      if (isSuccessResult(response.result)) {
        playSuccessBeep();
      } else {
        playErrorBuzz();
      }
    },
    [markActivity],
  );

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
      } catch (error) {
        setLastResponse(null);
        setErrorMessage(error instanceof Error ? error.message : "Ошибка проверки");
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
      setErrorMessage(error instanceof Error ? error.message : "Ошибка применения");
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
    markActivity();
    if (isCompleteCode(next)) {
      void runCheck(next);
    }
  };

  const tone = errorMessage ? "error" : resultToTone(lastResponse?.result ?? null);
  const statusText = errorMessage
    ? "ОШИБКА"
    : resultLabel(lastResponse?.result ?? null);
  const canRedeem = !busy && lastResponse?.result === "valid";

  return (
    <div className="cashier-shell" data-testid="cashier-shell">
      <header className="cashier-meta">
        <div>
          <div className="meta-label">Точка</div>
          <div className="meta-value" data-testid="point-id">
            {pointId}
          </div>
        </div>
        <div>
          <div className="meta-label">Сессия</div>
          <div className="meta-value">{formatTime(sessionStartedAt)}</div>
        </div>
        <div>
          <div className="meta-label">Активность</div>
          <div className="meta-value" data-testid="last-activity">
            {formatTime(lastActivityAt)}
          </div>
        </div>
        <div>
          <div className="meta-label">Heartbeat</div>
          <div className="meta-value" data-testid="last-heartbeat">
            {formatTime(lastHeartbeatAt)}
          </div>
        </div>
      </header>

      <main className="cashier-main">
        <p className="brand">Promocode Checker</p>
        <form className="scan-form" onSubmit={onSubmit}>
          <label className="sr-only" htmlFor="promocode-input">
            Промокод
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

        <div
          className={`status-panel tone-${tone}`}
          data-testid="status-panel"
          role="status"
          aria-live="polite"
        >
          <div className="status-label">{statusText}</div>
          <div className="status-code">{lastResponse?.code || code || "—"}</div>
          {errorMessage ? <div className="status-detail">{errorMessage}</div> : null}
          {lastResponse?.status ? (
            <div className="status-detail">DB: {lastResponse.status}</div>
          ) : null}
        </div>

        <button
          type="button"
          className="redeem-button"
          data-testid="redeem-button"
          disabled={!canRedeem}
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => void runRedeem()}
        >
          Применить скидку
        </button>

        {(locked || busy) && (
          <p className="lock-hint" data-testid="lock-hint">
            {busy ? "Запрос…" : "Пауза 1.5с"}
          </p>
        )}
      </main>
    </div>
  );
}
