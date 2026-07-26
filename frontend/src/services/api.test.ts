import {afterEach, describe, expect, it, vi} from "vitest";
import {acknowledgeAlert, startLiveAnalysis, stopLiveAnalysis} from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("dashboard API", () => {
  it("surfaces backend errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ok: false, status: 404, json: async () => ({error: "Alert not found"})}));
    await expect(acknowledgeAlert("missing")).rejects.toThrow("Alert not found");
  });

  it("controls the non-overlapping live analysis loop", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ok: true, json: async () => ({enabled: true})});
    vi.stubGlobal("fetch", fetchMock);
    await startLiveAnalysis();
    await stopLiveAnalysis();
    expect(fetchMock.mock.calls[0][0]).toBe("/api/live/start");
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/live/stop");
  });
});
