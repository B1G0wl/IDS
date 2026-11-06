document.getElementById("restartBtn").addEventListener("click", async () => {
  const res = await fetch("/restart_server", { method: "POST" });
  const data = await res.json();
  alert(data.message || "Server restarted!");
});
