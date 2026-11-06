export type Phase = "morning" | "midday" | "evening";

export function phaseOf(createdAt: string | undefined): Phase {
  const hour = createdAt ? Number(createdAt.slice(11, 13)) : 9;
  if (hour < 10) return "morning";
  if (hour < 15) return "midday";
  return "evening";
}

export function Window() {
  return (
    <svg className="window" viewBox="0 0 300 300" role="img" aria-label="A window onto campus, with sunlight coming through">
      <rect className="sky" x="14" y="14" width="272" height="262" />
      <circle className="sun" r="26" />
      <path className="far-hills" d="M14 214q60-34 124-14t148-20v96H14z" />
      <g className="tower">
        <rect x="192" y="110" width="30" height="120" />
        <rect x="197" y="86" width="20" height="26" />
        <path d="M200 86l7-30 7 30z" />
        <rect x="186" y="150" width="42" height="80" />
        <rect className="tower-window" x="203" y="118" width="8" height="16" rx="4" />
      </g>
      <path className="lawn" d="M14 240q130-22 272 0v36H14z" />
      <g className="branch">
        <path d="M14 66c40 6 70 2 112 26M56 72c10-14 24-20 38-22" fill="none" />
        <ellipse cx="96" cy="48" rx="13" ry="6" transform="rotate(-20 96 48)" />
        <ellipse cx="72" cy="58" rx="12" ry="6" transform="rotate(24 72 58)" />
        <ellipse cx="128" cy="96" rx="13" ry="6" transform="rotate(30 128 96)" />
        <ellipse cx="104" cy="74" rx="12" ry="6" transform="rotate(-16 104 74)" />
      </g>
      <g className="sash">
        <rect x="7" y="7" width="286" height="276" fill="none" strokeWidth="14" />
        <path d="M150 14v262M14 145h272" fill="none" strokeWidth="7" />
      </g>
    </svg>
  );
}

export function Plant() {
  return (
    <svg className="plant" viewBox="0 0 90 96" aria-hidden="true">
      <g className="leaves">
        <path d="M44 62C30 50 18 48 8 26c20 2 34 14 37 34z" />
        <path d="M46 62C42 40 44 22 52 6c10 18 8 38-4 56z" />
        <path d="M47 63c6-16 18-26 37-27-6 18-18 26-36 29z" />
      </g>
      <path className="pot" d="M24 62h44l-6 32H30z" />
      <path className="pot-rim" d="M21 58h50v8H21z" />
    </svg>
  );
}

export function Clock({ time }: { time: string | undefined }) {
  const [hours, minutes] = (time?.slice(11, 16) ?? "09:15").split(":").map(Number);
  const minuteAngle = minutes * 6;
  const hourAngle = (hours % 12) * 30 + minutes / 2;
  const marks = Array.from({ length: 12 }, (_, index) => index * 30);
  return (
    <svg className="clock" viewBox="0 0 120 120" role="img" aria-label={`Wall clock showing ${time?.slice(11, 16) ?? "09:15"}`}>
      <circle cx="60" cy="60" r="56" className="clock-rim" />
      <circle cx="60" cy="60" r="49" className="clock-face" />
      {marks.map((angle) => (
        <path key={angle} d="M60 15v7" transform={`rotate(${angle} 60 60)`} className="clock-mark" />
      ))}
      <path d="M60 60V34" className="clock-hour" style={{ transform: `rotate(${hourAngle}deg)` }} />
      <path d="M60 60V21" className="clock-minute" style={{ transform: `rotate(${minuteAngle}deg)` }} />
      <circle cx="60" cy="60" r="3.5" className="clock-pin" />
    </svg>
  );
}

export function Mug({ steaming }: { steaming: boolean }) {
  return (
    <svg className={`mug ${steaming ? "steaming" : ""}`} viewBox="0 0 150 150" role="img" aria-label="A cup of coffee on a saucer">
      <g className="steam" fill="none">
        <path d="M58 58c-8-12 8-16 0-30s8-16 2-26" />
        <path d="M78 58c-8-12 8-16 0-30s8-16 2-26" />
        <path d="M98 58c-8-12 8-16 0-30s8-16 2-26" />
      </g>
      <ellipse cx="75" cy="136" rx="66" ry="11" className="saucer" />
      <path d="M36 68h78v48a18 18 0 0 1-18 18H54a18 18 0 0 1-18-18z" className="mug-body" />
      <path d="M114 80h10a15 15 0 0 1 0 30h-10" fill="none" className="mug-handle" />
      <ellipse cx="75" cy="68" rx="39" ry="9" className="mug-rim" />
      <ellipse cx="75" cy="69" rx="33" ry="6" className="coffee" />
      <text x="75" y="110" textAnchor="middle" className="mug-mark">CC</text>
    </svg>
  );
}
