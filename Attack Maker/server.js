// Express proxy server for sending payloads to local network endpoints
// Usage:
//   npm init -y
//   npm install express node-fetch
//   node server.js

const express = require("express")
const fetch = require("node-fetch")
const app = express()
app.use(express.json())

const PORT = 3001
const ALLOWED_PREFIXES = ["http://10.", "http://192.168.", "http://172.16."]

app.post("/send", async (req, res) => {
    try {
        const { endpoint, payload } = req.body
        if (!endpoint || !payload) return res.status(400).send("missing endpoint or payload")

        const ok = ALLOWED_PREFIXES.some((p) => endpoint.startsWith(p))
        if (!ok) return res.status(400).send("endpoint not allowed by proxy whitelist")

        const r = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
        const text = await r.text()
        res.status(r.status).send(text)
    } catch (err) {
        console.error("proxy error", err)
        res.status(500).send("proxy error: " + err.message)
    }
})

app.listen(PORT, () => console.log("Proxy listening on http://localhost:" + PORT))
