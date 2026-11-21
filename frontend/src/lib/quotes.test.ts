import { describe, expect, it } from "vitest";
import { blocksFor, normalize, type Quote } from "./quotes";

const claim = (text: string): Quote => ({ label: "Obietnica zysku", text, tone: "claim" });

describe("blocksFor", () => {
  const blocks = [{ text: "Zarabiaj do 30%   miesięcznie" }, { text: "Inwestowanie wiąże się z ryzykiem." }, { text: "krótki" }];

  it("matches regardless of case and whitespace", () => {
    expect(blocksFor(claim("zarabiaj do 30% miesięcznie"), blocks)).toEqual([blocks[0]]);
  });

  it("matches a quote that spans a whole block of a longer quote", () => {
    expect(blocksFor(claim("Uwaga: inwestowanie wiąże się z ryzykiem. Czytaj regulamin."), blocks)).toEqual([blocks[1]]);
  });

  it("ignores quotes and blocks that are too short to be reliable", () => {
    expect(blocksFor(claim("krótki"), blocks)).toEqual([]);
  });
});

describe("normalize", () => {
  it("collapses whitespace", () => {
    expect(normalize("  A \n b ")).toBe("a b");
  });
});
