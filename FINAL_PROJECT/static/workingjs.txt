const socket = io("http://127.0.0.1:5000");
const tableBody = document.querySelector("#flowsTable tbody");
const totalFlowsEl = document.getElementById("totalFlows");
const totalAlertsEl = document.getElementById("totalAlerts");

let totalFlows = 0;
let totalAlerts = 0;

// 🔹 Load previous events
async function loadHistory() {
  try {
    const res = await fetch("/history");
    const data = await res.json();
    data.reverse().forEach(addFlowRow);
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}

// 🔹 Add new flow row to table
function addFlowRow(flow) {
  totalFlows++;
  totalFlowsEl.textContent = totalFlows;

  const tr = document.createElement("tr");
  if (flow.predicted_label !== "normal") {
    tr.classList.add("alert");
    totalAlerts++;
    totalAlertsEl.textContent = totalAlerts;
  }

  tr.innerHTML = `
    <td>${flow.ts || "-"}</td>
    <td>${flow.src}</td>
    <td>${flow.dst}</td>
    <td>${flow.pkts}</td>
    <td>${flow.bytes}</td>
    <td>${flow.predicted_label}</td>
    <td>${(flow.prob * 100).toFixed(1)}%</td>
  `;

  tableBody.prepend(tr);

  if (tableBody.rows.length > 200) {
    tableBody.deleteRow(200);
  }
}

// ✅ Delete All button logic
document.getElementById("clearBtn").addEventListener("click", async () => {
  if (!confirm("⚠️ Are you sure you want to delete all flow records?")) return;

  try {
    const res = await fetch("/clear_history", { method: "POST" });
    if (res.ok) {
      tableBody.innerHTML = "";
      totalFlows = 0;
      totalAlerts = 0;
      totalFlowsEl.textContent = "0";
      totalAlertsEl.textContent = "0";
      console.log("🧹 Cleared backend + dashboard data");
      alert("✅ All flow records deleted successfully!");
    } else {
      alert("❌ Failed to delete backend history.");
    }
  } catch (err) {
    console.error("Error clearing data:", err);
    alert("⚠️ Could not contact server. Check console for details.");
  }
});

// 🔹 Listen for live updates
socket.on("connect", () => console.log("✅ Connected to IDS stream"));
socket.on("new_flow", (flow) => addFlowRow(flow));

// 🔹 Initialize
loadHistory();
