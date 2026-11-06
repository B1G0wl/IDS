const socket = io("http://127.0.0.1:5000");

const pieCtx = document.getElementById("threatPie");
const confCtx = document.getElementById("confidenceTrend");
const flowCtx = document.getElementById("flowTrend");
const highRiskTable = document.getElementById("highRiskTable").querySelector("tbody");

let threatCounts = {};
let confidenceData = [];
let timeLabels = [];
let flowLabels = [];
let flowData = [];
let totalFlows = 0, alertCount = 0, totalConfidence = 0;

// === Initialize Charts ===
const pieChart = new Chart(pieCtx, {
  type: "doughnut",
  data: {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: ["#22c55e", "#ef4444", "#facc15", "#3b82f6", "#a855f7"]
    }]
  },
  options: {
    plugins: { legend: { position: "bottom" } },
    cutout: "65%"
  }
});

const confChart = new Chart(confCtx, {
  type: "line",
  data: { labels: [], datasets: [{ label: "Confidence", data: [], borderColor: "#38bdf8", backgroundColor: "rgba(56,189,248,0.15)", fill: true, tension: 0.3 }] },
  options: { scales: { y: { beginAtZero: true, max: 100 } } }
});

const flowChart = new Chart(flowCtx, {
  type: "bar",
  data: { labels: [], datasets: [{ label: "Flows", backgroundColor: "#22c55e", data: [] }] },
  options: { scales: { y: { beginAtZero: true } } }
});

// === Functions ===
async function loadHistory() {
  const res = await fetch("/history");
  const data = await res.json();
  data.slice(-200).forEach(flow => updateCharts(flow));
}

function updateCharts(flow) {
  totalFlows++;
  totalConfidence += (flow.prob || 0);
  document.getElementById("totalFlows").innerText = totalFlows;
  document.getElementById("avgConfidence").innerText = (totalConfidence / totalFlows * 100).toFixed(1) + "%";

  const label = flow.predicted_label || "unknown";
  threatCounts[label] = (threatCounts[label] || 0) + 1;

  if (label.toLowerCase() !== "normal" && label.toLowerCase() !== "benign") alertCount++;
  document.getElementById("alertCount").innerText = alertCount;

  // Pie chart
  pieChart.data.labels = Object.keys(threatCounts);
  pieChart.data.datasets[0].data = Object.values(threatCounts);
  pieChart.update();

  // Confidence line
  confidenceData.push((flow.prob || 0) * 100);
  timeLabels.push(flow.ts.slice(11, 19));
  if (confidenceData.length > 20) {
    confidenceData.shift();
    timeLabels.shift();
  }
  confChart.data.labels = timeLabels;
  confChart.data.datasets[0].data = confidenceData;
  confChart.update();

  // Flow trend (by minute)
  const minute = flow.ts.slice(11, 16);
  const idx = flowLabels.indexOf(minute);
  if (idx >= 0) flowData[idx]++;
  else {
    flowLabels.push(minute);
    flowData.push(1);
  }
  if (flowLabels.length > 30) {
    flowLabels.shift();
    flowData.shift();
  }
  flowChart.data.labels = flowLabels;
  flowChart.data.datasets[0].data = flowData;
  flowChart.update();

  // Table (show top recent flows)
  if (label.toLowerCase() !== "normal" && label.toLowerCase() !== "benign") {
    const row = document.createElement("tr");
    row.classList.add("danger");
    row.innerHTML = `
      <td>${flow.ts}</td>
      <td>${flow.src}</td>
      <td>${flow.dst}</td>
      <td>${flow.pkts}</td>
      <td>${flow.bytes}</td>
      <td>${label}</td>
      <td>${(flow.prob * 100).toFixed(2)}%</td>
    `;
    highRiskTable.prepend(row);
    if (highRiskTable.rows.length > 10) highRiskTable.deleteRow(10);
  }
}

// === SocketIO live updates ===
socket.on("new_flow", flow => updateCharts(flow));

// === Initial load ===
loadHistory();
