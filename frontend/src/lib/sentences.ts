// A sentence ends at . ! or ? (optionally after a closing bracket or quote) followed by a space
// and the start of the next sentence, so "92.1%" or "$22,250" never split.
const SENTENCE_BREAK = /(?<=[.!?]["”')\]]?)\s+(?=["“(]?[A-Z0-9$])/

export function splitSentences(text: string): string[] {
  return text
    .split(SENTENCE_BREAK)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
}
