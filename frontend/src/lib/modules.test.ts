import { describe, expect, it } from "vitest";
import { moduleInfo, riskBand } from "./modules";

describe("riskBand", () => {
  it.each([
    [0.95, "critical"],
    [0.85, "high"],
    [0.6, "medium"],
    [0.2, "low"],
  ])("maps %s to %s", (score, band) => {
    expect(riskBand(score)).toBe(band);
  });
});

describe("moduleInfo", () => {
  it("uses plain-language names and keeps unknown ids readable", () => {
    expect(moduleInfo("m3").name).toBe("Doradztwo bez zezwolenia");
    expect(moduleInfo("zzz").short).toBe("ZZZ");
  });
});
