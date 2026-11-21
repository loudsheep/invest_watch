const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 8080;

const ROUTES = {
  "/finfluencer-aurum": "finfluencer-aurum.html",
  "/landing-aurum-cfd": "landing-aurum-cfd.html",
  "/shadow-advisory-pwm": "shadow-advisory-pwm.html",
};

const server = http.createServer((req, res) => {
  const file = ROUTES[req.url];
  if (!file) {
    res.writeHead(404);
    res.end("Not found");
    return;
  }
  const filePath = path.join(__dirname, "public", file);
  fs.readFile(filePath, "utf-8", (err, data) => {
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
  // Deliberately no console.log in production frontend code (AGENTS.md),
  // but this is a standalone demo-fixtures server, not the frontend app.
  process.stdout.write(`demo-sites listening on :${PORT}\n`);
});
