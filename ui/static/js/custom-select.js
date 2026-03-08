let globalBindingsInitialized = false;
const menuState = new WeakMap();

function getMenuElements(root) {
  const state = menuState.get(root) || {};
  const menu = state.menu || root.querySelector(".custom-select-menu");
  const anchor = state.anchor || null;
  if (menu && !menuState.has(root)) {
    menuState.set(root, { menu, anchor: null });
  }
  return {
    menu,
    anchor,
  };
}

function attachMenuToBody(root) {
  const state = menuState.get(root);
  const trigger = root.querySelector(".custom-select-trigger");
  if (!state?.menu || !trigger) {
    return;
  }

  if (!state.anchor) {
    state.anchor = document.createElement("span");
    state.anchor.className = "custom-select-menu-anchor hidden";
    root.appendChild(state.anchor);
  }

  document.body.appendChild(state.menu);
  state.menu.classList.add("is-open");
  const rect = trigger.getBoundingClientRect();
  state.menu.style.position = "fixed";
  state.menu.style.top = `${rect.bottom + 8}px`;
  state.menu.style.left = `${rect.left}px`;
  state.menu.style.width = `${rect.width}px`;
}

function restoreMenu(root) {
  const state = menuState.get(root);
  if (!state?.menu || !state.anchor) {
    return;
  }

  state.menu.removeAttribute("style");
  state.menu.classList.remove("is-open");
  state.anchor.insertAdjacentElement("afterend", state.menu);
}

function repositionOpenMenus() {
  document.querySelectorAll(".custom-select.is-open").forEach((root) => {
    const state = menuState.get(root);
    const trigger = root.querySelector(".custom-select-trigger");
    if (!state?.menu || !trigger) {
      return;
    }
    const rect = trigger.getBoundingClientRect();
    state.menu.style.top = `${rect.bottom + 8}px`;
    state.menu.style.left = `${rect.left}px`;
    state.menu.style.width = `${rect.width}px`;
  });
}

function clearOpenHosts() {
  document.querySelectorAll(".custom-select-host-open").forEach((element) => {
    element.classList.remove("custom-select-host-open");
  });
}

function markOpenHost(root) {
  clearOpenHosts();
  const host = root.closest(".card, .page-header, .server-config-container");
  if (host) {
    host.classList.add("custom-select-host-open");
  }
}

function closeAllCustomSelects(except = null) {
  document.querySelectorAll(".custom-select.is-open").forEach((root) => {
    if (except && root === except) {
      return;
    }
    root.classList.remove("is-open");
    const trigger = root.querySelector(".custom-select-trigger");
    if (trigger) {
      trigger.setAttribute("aria-expanded", "false");
    }
    restoreMenu(root);
  });

  if (!except) {
    clearOpenHosts();
  }
}

function getSelectedLabel(select) {
  const option = select.options[select.selectedIndex] || select.options[0];
  return option ? option.textContent || "" : "";
}

function renderCustomSelect(select, root) {
  const trigger = root.querySelector(".custom-select-trigger");
  const value = root.querySelector(".custom-select-value");
  const { menu } = getMenuElements(root);
  if (!trigger || !value || !menu) {
    return;
  }

  const selectedValue = select.value;
  value.textContent = getSelectedLabel(select);
  menu.innerHTML = "";

  Array.from(select.options).forEach((option, index) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "custom-select-option";
    item.setAttribute("role", "option");
    item.dataset.value = option.value;
    item.dataset.index = String(index);
    item.textContent = option.textContent || "";
    item.disabled = option.disabled;

    const isSelected = option.value === selectedValue;
    item.setAttribute("aria-selected", isSelected ? "true" : "false");
    item.classList.toggle("is-selected", isSelected);

    menu.appendChild(item);
  });
}

function bindSelect(select, root) {
  const trigger = root.querySelector(".custom-select-trigger");
  const { menu } = getMenuElements(root);
  if (!trigger || !menu) {
    return;
  }

  if (!select.dataset.customSelectBound) {
    select.addEventListener("change", () => {
      renderCustomSelect(select, root);
    });
    select.dataset.customSelectBound = "true";
  }

  if (root.dataset.customSelectBound === "true") {
    return;
  }

  trigger.addEventListener("click", () => {
    if (select.disabled) {
      return;
    }
    const nextOpen = !root.classList.contains("is-open");
    closeAllCustomSelects(nextOpen ? root : null);
    root.classList.toggle("is-open", nextOpen);
    trigger.setAttribute("aria-expanded", nextOpen ? "true" : "false");
    if (nextOpen) {
      markOpenHost(root);
      attachMenuToBody(root);
    } else {
      clearOpenHosts();
    }
  });

  trigger.addEventListener("keydown", (event) => {
    if (select.disabled) {
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      const enabledOptions = Array.from(select.options).filter((option) => !option.disabled);
      if (!enabledOptions.length) {
        return;
      }

      const currentIndex = enabledOptions.findIndex((option) => option.value === select.value);
      const fallbackIndex = currentIndex >= 0 ? currentIndex : 0;
      const nextIndex = (fallbackIndex + direction + enabledOptions.length) % enabledOptions.length;
      select.value = enabledOptions[nextIndex].value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      trigger.click();
      return;
    }

    if (event.key === "Escape") {
      closeAllCustomSelects();
    }
  });

  menu.addEventListener("click", (event) => {
    const option = event.target instanceof HTMLElement ? event.target.closest(".custom-select-option") : null;
    if (!option || option.hasAttribute("disabled")) {
      return;
    }

    select.value = option.dataset.value || "";
    select.dispatchEvent(new Event("change", { bubbles: true }));
    closeAllCustomSelects();
    trigger.focus();
  });

  root.dataset.customSelectBound = "true";
}

function ensureSelectRoot(select) {
  let root = select.nextElementSibling;
  if (!(root instanceof HTMLElement) || !root.classList.contains("custom-select")) {
    root = document.createElement("div");
    root.className = "custom-select";
    root.innerHTML = `
      <button type="button" class="custom-select-trigger" aria-haspopup="listbox" aria-expanded="false">
        <span class="custom-select-value"></span>
        <span class="custom-select-chevron" aria-hidden="true"></span>
      </button>
      <div class="custom-select-menu" role="listbox"></div>
    `;
    select.insertAdjacentElement("afterend", root);
  }

  const menu = root.querySelector(".custom-select-menu");
  if (menu) {
    const existingState = menuState.get(root) || {};
    menuState.set(root, {
      menu,
      anchor: existingState.anchor || null,
    });
  }

  root.classList.toggle("is-lang-select", select.classList.contains("lang-select"));
  root.classList.toggle("is-server-select", select.classList.contains("server-selector"));

  return root;
}

export function enhanceCustomSelects(root = document) {
  if (!globalBindingsInitialized) {
    document.addEventListener("click", (event) => {
      const target = event.target instanceof HTMLElement ? event.target : null;
      if (!target?.closest(".custom-select")) {
        closeAllCustomSelects();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeAllCustomSelects();
      }
    });

    window.addEventListener("resize", repositionOpenMenus);
    window.addEventListener("scroll", repositionOpenMenus, true);

    globalBindingsInitialized = true;
  }

  root.querySelectorAll("select").forEach((select) => {
    if (!(select instanceof HTMLSelectElement)) {
      return;
    }

    select.classList.add("custom-select-native");
    const customRoot = ensureSelectRoot(select);
    customRoot.classList.toggle("is-disabled", select.disabled);

    const labelledBy = select.getAttribute("aria-labelledby");
    const ariaLabel = select.getAttribute("aria-label");
    const trigger = customRoot.querySelector(".custom-select-trigger");
    const menu = customRoot.querySelector(".custom-select-menu");
    if (labelledBy) {
      trigger?.setAttribute("aria-labelledby", labelledBy);
    } else if (ariaLabel) {
      trigger?.setAttribute("aria-label", ariaLabel);
    }
    if (select.id) {
      menu?.setAttribute("id", `${select.id}-custom-menu`);
      trigger?.setAttribute("aria-controls", `${select.id}-custom-menu`);
    }

    renderCustomSelect(select, customRoot);
    bindSelect(select, customRoot);
  });
}
