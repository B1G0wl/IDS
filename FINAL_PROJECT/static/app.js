document.addEventListener("DOMContentLoaded", () => {
  const navItems = document.querySelectorAll(".sidebar li");
  const main = document.querySelector("main");

  async function loadPage(page) {
    try {
      const res = await fetch(`/pages/${page}`);
      const html = await res.text();
      main.innerHTML = html;

      // Update active state
      navItems.forEach(li => li.classList.remove("active"));
      document.querySelector(`[data-page="${page}"]`).classList.add("active");
    } catch (err) {
      main.innerHTML = "<h2>⚠️ Page not found</h2>";
      console.error(err);
    }
  }

  navItems.forEach(li => {
    li.addEventListener("click", () => {
      const page = li.getAttribute("data-page");
      loadPage(page);
    });
  });

  // Load dashboard on startup
  loadPage("dashboard.html");
});
