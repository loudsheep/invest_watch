import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Loading from "../components/Loading";
import { quotesFor } from "../components/FindingFacts";
import QueryError from "../components/QueryError";
import ShotOverlay from "../components/ShotOverlay";
import { API_URL, api } from "../lib/api";

export default function FindingScreenshot() {
  const { id } = useParams();
  const { data, isError, refetch } = useQuery({
    queryKey: ["finding", id],
    queryFn: () => api.getFinding(Number(id)),
    enabled: !!id,
  });

  if (isError) return <QueryError onRetry={() => refetch()} />;
  if (!data) return <Loading />;
  const src = data.screenshot_url && (data.screenshot_url.startsWith("http") ? data.screenshot_url : `${API_URL}${data.screenshot_url}`);

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
          {src ? <ShotOverlay src={src} styles={data.computed_styles} quotes={quotesFor(data)} /> : <p className="empty">Brak zrzutu ekranu.</p>}
        </div>
      </section>
    </>
  );
}
