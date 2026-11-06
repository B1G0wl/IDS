const socket = io(document.getElementById("serverUrl").value);
const alertsBody = document.getElementById("alerts-body");
const normalsBody = document.getElementById("normals-body");
const alertCount = document.getElementById("alertCount");
const injLog = document.getElementById("inj_log");

let alerts = [];
let normals = [];
let continuous = null;

// helper: create rows
function makeRow(f, type) {
  const tr = document.createElement("tr");
  tr.className = type;
  const cells =
    type === "normal"
      ? `<td>${f.ts}</td><td>${f.src}</td><td>${f.dst}</td><td>${f.pkts}</td><td>${f.bytes}</td><td>${f.entropy || ""}</td>`
      : `<td>${f.ts}</td><td>${f.src}</td><td>${f.dst}</td><td>${f.pkts}</td><td>${f.predicted_label}</td><td>${f.prob}</td><td>${f.entropy}</td>`;
  tr.innerHTML = cells;
  return tr;
}

// add flow to UI
function addFlow(flow) {
  if (flow.predicted_label && flow.predicted_label !== "normal") {
    alerts.unshift(flow);
    alertsBody.prepend(makeRow(flow, flow.predicted_label));
    alertCount.textContent = alerts.length;
  } else {
    normals.unshift(flow);
    normalsBody.prepend(makeRow(flow, "normal"));
  }
}

// socket event
socket.on("new_flow", (flow) => {
  addFlow(flow);
});

// send attack to server
async function sendAttack(flow) {
  const url = document.getElementById("serverUrl").value + "/ingest";
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(flow),
  });
  const text = await res.text();
  injLog.prepend(document.createTextNode(`[${new Date().toISOString()}] ${text}\n`));
}

// build flow from form
function getFlow() {
  return {
    ts: new Date().toISOString(),
    src: document.getElementById("inj_src").value,
    dst: document.getElementById("inj_dst").value,
    duration: parseFloat(document.getElementById("inj_duration").value),
    pkts: parseInt(document.getElementById("inj_pkts").value),
    bytes: parseInt(document.getElementById("inj_bytes").value),
    syn: parseInt(document.getElementById("inj_syn").value),
    payload: btoa(document.getElementById("inj_payload").value),
    meta: { attack: true },
  };
}

// event listeners
document.getElementById("sendSingle").onclick = () => sendAttack(getFlow());
document.getElementById("sendBurst").onclick = async () => {
  for (let i = 0; i < 5; i++) {
    await sendAttack(getFlow());
    await new Promise((r) => setTimeout(r, 150));
  }
};
document.getElementById("startCont").onclick = () => {
  continuous = setInterval(() => sendAttack(getFlow()), 500);
  document.getElementById("startCont").disabled = true;
  document.getElementById("stopCont").disabled = false;
};
document.getElementById("stopCont").onclick = () => {
  clearInterval(continuous);
  continuous = null;
  document.getElementById("startCont").disabled = false;
  document.getElementById("stopCont").disabled = true;
};
