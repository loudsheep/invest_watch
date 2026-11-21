import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Loading from "../components/Loading";
import { quotesFor } from "../components/FindingFacts";
import QueryError from "../components/QueryError";
import ScreenshotViewer from "../components/ScreenshotViewer";
import { api } from "../lib/api";

export default function FindingScreenshot() {
  const { id } = useParams();
  const { data, isError, refetch } = useQuery({
    queryKey: ["finding", id],
    queryFn: () => api.getFinding(Number(id)),
    enabled: !!id,
  });

  if (isError) return <QueryError onRetry={() => refetch()} />;
  if (!data) return <Loading />;

  return (
    <>
      <div className="page__header">
        <div>
          <p className="crumbs">
            <Link to={`/findings/${data.id}`}>← Finding #{data.id}</Link>
          </p>
          <h1 className="page__title">Pełny zrzut strony</h1>
          <p className="page__sub">{data.document_url}</p>
        </div>
      </div>
      <section className="panel">
        <div className="panel__body">
          {data.screenshot_url ? <ScreenshotViewer finding={data} quotes={quotesFor(data)} /> : <p className="empty">Brak zrzutu ekranu.</p>}
        </div>
      </section>
    </>
  );
}
