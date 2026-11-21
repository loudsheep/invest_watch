import pl from "../i18n/pl.json";

export default function Loading({ label }: { label?: string }) {
  return (
    <p className="loading" role="status">
      <span className="spinner" aria-hidden="true" />
      {label ?? pl["common.loading"]}
    </p>
  );
}
