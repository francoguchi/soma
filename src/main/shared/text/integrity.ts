// Detect common UTF-8/code-page corruption without changing authoritative strings.
export const textCorruption = /\uFFFD|\u00C2[\u00A0-\u00BF]|\u00C3[\u0080-\u00BF]|\u00E2[\u0080-\u00BF\u20AC\u2122]/u;
export function hasTextCorruption(text: string): boolean {return textCorruption.test(text);}
