document.getElementById("uploadBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("datasetFile");
  if (!fileInput.files.length) {
    alert("Select a CSV file first!");
    return;
  }
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  const res = await fetch("/upload_dataset", { method: "POST", body: formData });
  const data = await res.json();
  document.getElementById("uploadStatus").textContent = data.message || "Upload complete.";
});
