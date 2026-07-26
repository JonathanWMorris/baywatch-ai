import {afterEach, describe, expect, it, vi} from "vitest";
import {acknowledgeAlert, analyzeMedia} from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("dashboard API", () => {
  it("sends camera media as multipart data", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ok: true, json: async () => ({assessment: {risk_level: "low"}})});
    vi.stubGlobal("fetch", fetchMock);
    const clip = new File(["clip"], "beach.mp4", {type: "video/mp4"});
    await analyzeMedia("camera_2", clip);
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(init.body.get("camera_id")).toBe("camera_2");
    expect(init.body.get("video").name).toBe("beach.mp4");
  });

  it("surfaces backend errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ok: false, status: 404, json: async () => ({error: "Alert not found"})}));
    await expect(acknowledgeAlert("missing")).rejects.toThrow("Alert not found");
  });
});
