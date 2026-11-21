export interface Quote {
  label: string;
  text: string;
  tone: "claim" | "warning";
}

export interface TextBlock {
  text?: string;
}

const MIN_BLOCK_LENGTH = 12;

export const normalize = (text: string) => text.toLowerCase().replace(/\s+/g, " ").trim();

/** Page text blocks that contain a quote (or are contained in it, for quotes spanning several blocks). */
export function blocksFor<T extends TextBlock>(quote: Quote, blocks: T[]): T[] {
  const wanted = normalize(quote.text);
  if (wanted.length < MIN_BLOCK_LENGTH) return [];
  return blocks.filter((block) => {
    const text = normalize(block.text ?? "");
    return text.length >= MIN_BLOCK_LENGTH && (text.includes(wanted) || wanted.includes(text));
  });
}
