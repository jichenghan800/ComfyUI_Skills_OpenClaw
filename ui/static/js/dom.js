export function getElements() {
  const $ = window.jQuery;
  return {
    langSelect: $("#lang-select"),
    // ── View containers ──
    viewMain: $("#view-main"),
    viewEditor: $("#view-editor"),
    // ── Server panel ──
    serverSelector: $("#server-selector"),
    serverEnabledToggle: $("#server-enabled-toggle"),
    serverEnabledLabel: $("#server-enabled-label"),
    deleteServerBtn: $("#delete-server-btn"),
    currentServerActions: $("#current-server-actions"),
    // ── Edit Panel elements ──
    btnEditServer: $("#btn-edit-server"),
    btnCancelEditServer: $("#btn-cancel-edit-server"),
    currentServerConfigPanel: $("#current-server-config-panel"),
    // ── Config ──
    configUrl: $("#config-url"),
    configOutput: $("#config-out"),
    saveConfigButton: $("#save-config-btn"),
    // ── Workflow list ──
    workflowList: $("#workflow-list"),
    workflowSummary: $("#workflow-summary"),
    addWorkflowBtn: $("#add-workflow-btn"),
    // ── Editor (View 2) ──
    editorBackBtn: $("#editor-back-btn"),
    editorModeBadge: $("#editor-mode-badge"),
    editorProgressHint: $("#editor-progress-hint"),
    editorStep1: $("#editor-step-1"),
    editorStep2: $("#editor-step-2"),
    editorStep3: $("#editor-step-3"),
    uploadZone: $("#upload-zone"),
    fileUpload: $("#file-upload"),
    mappingSection: $("#mapping-section"),
    mappingSearch: $("#mapping-search"),
    mappingNodeSort: $("#mapping-node-sort"),
    mappingParamSort: $("#mapping-param-sort"),
    mappingExposedOnly: $("#mapping-exposed-only"),
    mappingRequiredOnly: $("#mapping-required-only"),
    mappingExposeRecommendedButton: $("#mapping-expose-recommended"),
    mappingExposeVisibleButton: $("#mapping-expose-visible"),
    mappingUnexposeVisibleButton: $("#mapping-unexpose-visible"),
    mappingCollapseAllButton: $("#mapping-collapse-all"),
    mappingExpandAllButton: $("#mapping-expand-all"),
    mappingResetFiltersButton: $("#mapping-reset-filters"),
    mappingSummary: $("#mapping-summary"),
    workflowId: $("#wf-id"),
    workflowDescription: $("#wf-desc"),
    nodesContainer: $("#nodes-container"),
    saveWorkflowButton: $("#save-workflow-btn"),
    toastContainer: $("#toast-container"),
  };
}
