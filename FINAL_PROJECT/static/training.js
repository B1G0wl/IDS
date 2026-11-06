document.getElementById("trainBtn").addEventListener("click", async () => {
  document.getElementById("trainStatus").textContent = "Training started...";
  const res = await fetch("/train_model", { method: "POST" });
  const data = await res.json();
  document.getElementById("trainStatus").textContent = `✅ ${data.message || "Training completed!"}`;
});
