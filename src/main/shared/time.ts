export function displayTime(utcSeconds: number | null, options: {timeZone?: string; locale?: string} = {}): string {
  if (utcSeconds === null) return 'Unknown';
  if (!Number.isSafeInteger(utcSeconds)) return 'Time unavailable';
  try {return new Intl.DateTimeFormat(options.locale, {dateStyle: 'medium', timeStyle: 'medium', ...(options.timeZone ? {timeZone: options.timeZone} : {})}).format(new Date(utcSeconds * 1000));}
  catch {return 'Time unavailable';}
}
