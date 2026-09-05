const SECRET_KEYS = new Set(['usertoken','token','key','access_token']);

export function redactUrl(value: string): string {
  try {
    const url = new URL(value);
    for (const [key] of url.searchParams) {
      if (SECRET_KEYS.has(key.toLowerCase())) url.searchParams.set(key, '[REDACTED]');
    }
    return url.toString();
  } catch {
    return '<invalid-url>';
  }
}

export function redactText(value: string): string {
  return value.replace(/(userToken|token|key|access_token)=([^&\s]+)/gi, '$1=[REDACTED]');
}
