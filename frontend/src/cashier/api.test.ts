import { describe, expect, it } from "vitest";

import { parseHealthPayload } from "./api";

describe("parseHealthPayload", () => {
  it("returns ready when database and schema are ok", () => {
    expect(parseHealthPayload({ status: "ok", database: "ok", schema: "ok" })).toEqual({
      state: "ready",
      message: "Ready",
      ready: true,
    });
  });

  it("returns degraded when schema is missing", () => {
    expect(parseHealthPayload({ status: "degraded", database: "ok", schema: "missing" })).toEqual({
      state: "degraded",
      message: "DB not initialized",
      ready: false,
    });
  });

  it("returns offline when database is down", () => {
    expect(parseHealthPayload({ status: "degraded", database: "error", schema: "unknown" })).toEqual({
      state: "offline",
      message: "Database offline",
      ready: false,
    });
  });
});
