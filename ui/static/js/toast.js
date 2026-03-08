const TOAST_META = {
  success: { icon: "✓", title: "Success" },
  error: { icon: "!", title: "Error" },
  info: { icon: "i", title: "Notice" },
};

const MAX_TOAST_COUNT = 4;

export function showToast(message, type = "success", duration = 3000) {
  const container = document.getElementById("toast-container");
  if (!container) {
    return;
  }

  const normalizedType = TOAST_META[type] ? type : "info";
  const meta = TOAST_META[normalizedType];

  const toast = document.createElement("div");
  toast.className = `toast ${normalizedType}`;
  toast.setAttribute("role", normalizedType === "error" ? "alert" : "status");
  toast.setAttribute("aria-live", normalizedType === "error" ? "assertive" : "polite");

  const icon = document.createElement("span");
  icon.className = "toast-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = meta.icon;

  const body = document.createElement("div");
  body.className = "toast-body";

  const title = document.createElement("p");
  title.className = "toast-title";
  title.textContent = meta.title;

  const text = document.createElement("p");
  text.className = "toast-message";
  text.textContent = String(message);

  const progress = document.createElement("div");
  progress.className = "toast-progress";
  progress.style.animationDuration = `${duration}ms`;

  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "toast-close";
  closeButton.setAttribute("aria-label", "Close notification");
  closeButton.textContent = "×";

  body.appendChild(title);
  body.appendChild(text);
  toast.appendChild(icon);
  toast.appendChild(body);
  toast.appendChild(closeButton);
  toast.appendChild(progress);

  container.appendChild(toast);

  while (container.children.length > MAX_TOAST_COUNT) {
    container.removeChild(container.firstElementChild);
  }

  let closeTimerId = null;
  let startTime = Date.now();
  let remaining = duration;

  function closeToast() {
    if (toast.classList.contains("closing")) {
      return;
    }
    toast.classList.add("closing");
    window.setTimeout(() => toast.remove(), 260);
  }

  function startCloseTimer(ms) {
    window.clearTimeout(closeTimerId);
    startTime = Date.now();
    closeTimerId = window.setTimeout(closeToast, ms);
  }

  function pauseTimer() {
    window.clearTimeout(closeTimerId);
    remaining = Math.max(0, remaining - (Date.now() - startTime));
    toast.classList.add("is-paused");
  }

  function resumeTimer() {
    if (toast.classList.contains("closing")) {
      return;
    }
    toast.classList.remove("is-paused");
    startCloseTimer(remaining);
  }

  closeButton.addEventListener("click", closeToast);
  toast.addEventListener("mouseenter", pauseTimer);
  toast.addEventListener("mouseleave", resumeTimer);

  startCloseTimer(duration);
}
