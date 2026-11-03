// Matches AI text rendered by RichText, where "[A1]" becomes a separate "A1" label.
export function aiText(text: string) {
  const want = text.replace(/\s*\[([^\]]+)\]/g, (_, ids: string) => ids.split(/\s*,\s*/).join(''))
  return (_content: string, element: Element | null) =>
    element?.textContent === want &&
    ![...element.children].some((child) => child.textContent === want)
}
