document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((el, i) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0.55";
    }, 4000 + i * 200);
  });
});
