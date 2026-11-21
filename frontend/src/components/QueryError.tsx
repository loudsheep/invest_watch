import pl from "../i18n/pl.json";

interface QueryErrorProps {
  onRetry?: () => void;
  message?: string;
}

export default function QueryError({ onRetry, message }: QueryErrorProps) {
  return (
    <div className="notice" role="alert">
      <p>{message ?? pl["common.error"]}</p>
      {onRetry && (
        <button className="btn btn--secondary btn--small" onClick={onRetry}>
          {pl["common.retry"]}
        </button>
      )}
    </div>
  );
}
