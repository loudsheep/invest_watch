const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 8080;
const PUBLIC_DIR = path.join(__dirname, "public");

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
    res.end(JSON.stringify(pages().map((p) => `/${p}`)));
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
    res.end(data);
  });
});

server.listen(PORT, () => {
  process.stdout.write(`demo-sites listening on :${PORT}\n`);
});
