import {afterEach, describe, expect, it, vi} from "vitest";
import {acknowledgeAlert, getWatchStatus, sendWatchAction, startLiveAnalysis, stopLiveAnalysis} from "./api";

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

  it("fetches smartwatch status and triggers wrist actions", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ok: true, json: async () => ({risk_level: "high", device_target: "Lifeguard Smart Watch"})})
      .mockResolvedValueOnce({ok: true, json: async () => ({success: true, action: "trigger_whistle"})});
    vi.stubGlobal("fetch", fetchMock);

    const status = await getWatchStatus();
    expect(status.risk_level).toBe("high");

    const actionResult = await sendWatchAction("trigger_whistle");
    expect(actionResult.success).toBe(true);
    expect(fetchMock.mock.calls[1][0]).toBe("/api/watch/action");
  });
});

