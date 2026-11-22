const INTERNAL_ORIGINS = ["http://demo-sites:8080", "http://nordik-brokr-demo.local:8080"];

export function publicUrl(url: string, demoSitesUrl: string | undefined = import.meta.env.VITE_DEMO_SITES_URL): string {
  if (!demoSitesUrl) return url;
  const origin = INTERNAL_ORIGINS.find((o) => url === o || url.startsWith(`${o}/`));
  return origin ? demoSitesUrl.replace(/\/$/, "") + url.slice(origin.length) : url;
}
