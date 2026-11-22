import { describe, expect, it } from "vitest";
import { publicUrl } from "./demoSites";

describe("publicUrl", () => {
  const demo = "https://investwatch-demo.b.solvro.pl/";

  it("maps internal demo-sites hosts to the public address", () => {
    expect(publicUrl("http://demo-sites:8080/landing-aurum-cfd", demo)).toBe("https://investwatch-demo.b.solvro.pl/landing-aurum-cfd");
    expect(publicUrl("http://nordik-brokr-demo.local:8080/clone-nordik", demo)).toBe("https://investwatch-demo.b.solvro.pl/clone-nordik");
  });

  it("leaves other urls and unconfigured setups untouched", () => {
    expect(publicUrl("https://example.com/page", demo)).toBe("https://example.com/page");
    expect(publicUrl("http://demo-sites:80800/x", demo)).toBe("http://demo-sites:80800/x");
    expect(publicUrl("http://demo-sites:8080/x", undefined)).toBe("http://demo-sites:8080/x");
  });
});
