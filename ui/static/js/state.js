function normalizeLanguage(language) {
  if (!language) {
    return "en";
  }

  const value = String(language).toLowerCase();
  if (value === "zh" || value === "zh-cn" || value === "zh_hans") {
    return "zh";
  }
  if (value === "zh_hant" || value === "zh-tw" || value === "zh-hant") {
    return "zh_hant";
  }
  return "en";
}

const state = {
  currentLang: normalizeLanguage(localStorage.getItem("ui-lang")),
  currentUploadData: null,
  schemaParams: {},
  workflows: [],
  editingWorkflowId: null,
  // Multi-server state
  servers: [],
  currentServerId: localStorage.getItem("ui-server") || null,
  defaultServerId: null,
};

export function getState() {
  return state;
}

export function setLanguage(language) {
  const normalized = normalizeLanguage(language);
  state.currentLang = normalized;
  localStorage.setItem("ui-lang", normalized);
}

export function toggleLanguage() {
  const nextLanguage = state.currentLang === "en" ? "zh" : "en";
  setLanguage(nextLanguage);
  return nextLanguage;
}

export function setUploadData(workflowData) {
  state.currentUploadData = workflowData;
}

export function setSchemaParams(schemaParams) {
  state.schemaParams = schemaParams;
}

export function updateSchemaParam(key, field, value) {
  if (!state.schemaParams[key]) {
    return;
  }
  state.schemaParams[key][field] = value;
}

export function resetMappingState() {
  state.currentUploadData = null;
  state.schemaParams = {};
}

export function setWorkflows(workflows) {
  state.workflows = workflows;
}

export function setEditingWorkflowId(workflowId) {
  state.editingWorkflowId = workflowId;
}

// Multi-server state management

export function setServers(servers) {
  state.servers = servers;
}

export function setDefaultServerId(defaultServerId) {
  state.defaultServerId = defaultServerId;
}

export function setCurrentServerId(serverId) {
  state.currentServerId = serverId;
  if (serverId) {
    localStorage.setItem("ui-server", serverId);
  }
}

export function getCurrentServerId() {
  return state.currentServerId || state.defaultServerId || (state.servers[0]?.id ?? null);
}

export function getCurrentServer() {
  const sid = getCurrentServerId();
  return state.servers.find((s) => s.id === sid) || null;
}
