export function HelpTooltip({ content }: { content: string }) {
  return <span className="help-tooltip" title={content} aria-label={content} role="img">?</span>;
}

export function HelpLabel({ children, content }: { children: string; content: string }) {
  return <span className="help-label">{children}<HelpTooltip content={content} /></span>;
}
