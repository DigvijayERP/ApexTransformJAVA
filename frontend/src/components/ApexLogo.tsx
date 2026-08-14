/* Copied verbatim from aux_web_version/frontend/src/shared/components/ApexLogo.tsx
   so both APEX apps carry the identical mark. Keep them in sync by copying
   again rather than editing one side. */

interface ApexLogoProps {
  size?: number;
  className?: string;
}

/**
 * 2bEcho mark — two offset A-chevrons (stroke only, no fill) that create an
 * echo/depth effect ("A in motion, legacy shifts to modern").
 *
 * Chevron colours come from CSS variables (--logo-chevron-back /
 * --logo-chevron-front), so the mark themes automatically in light and dark —
 * no hardcoded colours in this component.
 */
export function ApexLogo({ size = 26, className }: ApexLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Back chevron — the "echo" */}
      <polyline
        points="34,80 60,34 86,80"
        fill="none"
        stroke="var(--logo-chevron-back)"
        strokeWidth="9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Front chevron */}
      <polyline
        points="16,80 42,34 68,80"
        fill="none"
        stroke="var(--logo-chevron-front)"
        strokeWidth="9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
