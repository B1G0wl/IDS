// frontend.js — logic for index.html

const PRESETS = {
    normal: { src: "192.168.0.101", dst: "192.168.0.10", duration: 1.2, pkts: 8, bytes: 1200, syn: 0, packet_rate: 6.7, byte_rate: 1000 },
    syn_flood: { src: "192.168.0.150", dst: "192.168.0.20", duration: 0.6, pkts: 2000, bytes: 160000, syn: 1800, packet_rate: 3333.3, byte_rate: 266666.7 },
    udp_flood: { src: "10.0.0.45", dst: "192.168.0.30", duration: 5, pkts: 40000, bytes: 5000000, syn: 0, packet_rate: 8000, byte_rate: 1000000 },
    probe: { src: "172.16.5.10", dst: "192.168.0.0", duration: 0.05, pkts: 3, bytes: 180, syn: 3, packet_rate: 60, byte_rate: 3600 },
    u2r: { src: "192.168.0.110", dst: "192.168.0.200", duration: 0.3, pkts: 12, bytes: 15000, syn: 0, packet_rate: 40, byte_rate: 50000 },
    r2l: { src: "203.0.113.77", dst: "192.168.0.50", duration: 0.1, pkts: 4, bytes: 240, syn: 1, packet_rate: 40, byte_rate: 2400 }
};

function buildPayload() {
    const preset = document.getElementById('preset').value;
    const ep = document.getElementById('endpoint').value.trim();
    const src = document.getElementById('src').value.trim();
    const dst = document.getElementById('dst').value.trim();
    const duration = Number(document.getElementById('duration').value);
    const pkts = Number(document.getElementById('pkts').value);
    const bytes = Number(document.getElementById('bytes').value);
    const syn = Number(document.getElementById('syn').value);
    let payload = Object.assign({}, PRESETS[preset]);
    payload.src = src; payload.dst = dst; payload.duration = duration; payload.pkts = pkts; payload.bytes = bytes; payload.syn = syn;
    try {
        const extra = JSON.parse(document.getElementById('extra').value || '{}');
        payload = Object.assign(payload, extra);
    } catch (e) {
        alert('Extra fields must be valid JSON');
    }
    return { endpoint: ep, payload };
}

function buildPowerShell({ endpoint, payload }) {
    const parts = Object.entries(payload).map(([k, v]) => {
        if (typeof v === 'string') return `    ${k}="${v}"`;
        return `    ${k}=${v}`;
    }).join('\n');
    const body = `@{\n${parts}\n} | ConvertTo-Json`;
    return `Invoke-WebRequest -Uri "${endpoint}" -Method POST -Body (${body}) -ContentType "application/json"`;
}

document.getElementById('preset').addEventListener('change', (e) => {
    const p = PRESETS[e.target.value];
    document.getElementById('src').value = p.src;
    document.getElementById('dst').value = p.dst;
    document.getElementById('duration').value = p.duration;
    document.getElementById('pkts').value = p.pkts;
    document.getElementById('bytes').value = p.bytes;
    document.getElementById('syn').value = p.syn;
    document.getElementById('extra').value = JSON.stringify({ packet_rate: p.packet_rate, byte_rate: p.byte_rate }, null, 2);
});

document.getElementById('build').addEventListener('click', () => {
    const data = buildPayload();
    const cmd = buildPowerShell(data);
    document.getElementById('cmd').textContent = cmd;
    document.getElementById('status').textContent = 'Built command';
});

document.getElementById('copy').addEventListener('click', async () => {
    const cmd = document.getElementById('cmd').textContent;
    try {
        await navigator.clipboard.writeText(cmd);
        document.getElementById('status').textContent = 'Copied to clipboard ✅';
    } catch (e) { document.getElementById('status').textContent = 'Copy failed — manual select & copy.' }
});

document.getElementById('send').addEventListener('click', async () => {
    const data = buildPayload();
    document.getElementById('status').textContent = 'Sending to proxy...';
    try {
        const resp = await fetch('http://localhost:3001/send', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        const text = await resp.text();
        document.getElementById('status').textContent = `Proxy replied [${resp.status}]: ${text}`;
    } catch (e) { document.getElementById('status').textContent = 'Send failed: ' + e.message }
});

// initialize default preset values
(function () { document.getElementById('preset').dispatchEvent(new Event('change')); })();
