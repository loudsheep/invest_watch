import pl from "../i18n/pl.json";

interface QueryErrorProps {
  onRetry?: () => void;
  message?: string;
}

export default function QueryError({ onRetry, message }: QueryErrorProps) {
  return (
    <div className="notice" role="alert">
      <p className="notice__text">{message ?? pl["common.error"]}</p>
      {onRetry && (
        <button className="btn btn--ghost btn--small" onClick={onRetry}>
          {pl["common.retry"]}
        </button>
      )}
    </div>
  );
}
