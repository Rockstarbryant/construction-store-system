const DISPLAY_TZ = "Africa/Nairobi";

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  const datePart = new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: DISPLAY_TZ,
  }).format(d);
  const timePart = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: DISPLAY_TZ,
  }).format(d);
  return `${datePart}, ${timePart} EAT`;
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: DISPLAY_TZ,
  }).format(d);
}

export function formatDuration(fromIso: string): string {
  const from = new Date(fromIso).getTime();
  const now = Date.now();
  const diffMinutes = Math.max(0, Math.floor((now - from) / 60000));
  if (diffMinutes < 60) return `${diffMinutes}m`;
  const hours = Math.floor(diffMinutes / 60);
  if (hours < 24) return `${hours}h ${diffMinutes % 60}m`;
  const days = Math.floor(hours / 24);
  return `${days}d ${hours % 24}h`;
}
