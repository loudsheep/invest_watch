const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 8080;
const PUBLIC_DIR = path.join(__dirname, "public");
const CLONE_HOST = process.env.CLONE_HOST || "nordik-brokr-demo.local";
const RISK_WARNING = "Inwestowanie w CFD wiąże się z ryzykiem utraty kapitału.";
let riskWarningVisible = true;

const pages = () =>
  fs
    .readdirSync(PUBLIC_DIR)
    .filter((f) => f.endsWith(".html"))
    .map((f) => f.slice(0, -".html".length))
    .sort();

const server = http.createServer((req, res) => {
  const route = req.url.split("?")[0];

  if (route === "/index.json") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(pages().map((p) => (p.startsWith("clone-") ? `http://${CLONE_HOST}:${PORT}/${p}` : `/${p}`))));
    return;
  }

  if (route === "/__toggle-risk") {
    riskWarningVisible = !riskWarningVisible;
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ riskWarningVisible }));
    return;
  }

  const name = route.slice(1);
  if (!pages().includes(name)) {
    res.writeHead(404);
    res.end("Not found");
    return;
  }
  fs.readFile(path.join(PUBLIC_DIR, `${name}.html`), "utf-8", (err, data) => {
    if (err) {
      res.writeHead(500);
      res.end("Server error");
      return;
    }
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(data.replace("{{RISK_WARNING}}", riskWarningVisible ? RISK_WARNING : ""));
  });
});

server.listen(PORT, () => {
  process.stdout.write(`demo-sites listening on :${PORT}\n`);
});
