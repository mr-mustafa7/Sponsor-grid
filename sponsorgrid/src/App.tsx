import React, { useMemo, useState } from "react";
import { CheckCircle2, ShieldCheck } from "lucide-react";
import { ActionCenterView } from "./components/ActionCenterView";
import { CohortSimulatorView } from "./components/CohortSimulatorView";
import { DossierModal } from "./components/DossierModal";
import { FeasibilityBoardView } from "./components/FeasibilityBoardView";
import { ModalPydanticEngineView } from "./components/ModalPydanticEngineView";
import { PipelineView } from "./components/PipelineView";
import { INITIAL_ACTION_ITEMS, INITIAL_SYNTHETIC_PATIENTS, SITES } from "./data/syntheticData";
import { ActionItem, ActiveTabType } from "./types";

const TABS: { id: ActiveTabType; label: string }[] = [
  { id: "feasibility_board", label: "Board" },
  { id: "ten_stage_pipeline", label: "Pipeline" },
  { id: "modal_pydantic_agent", label: "Modal" },
  { id: "action_center", label: "Actions" },
  { id: "cohort_simulator", label: "Simulator" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTabType>("feasibility_board");
  const [gatewayRuleOn, setGatewayRuleOn] = useState(true);
  const [humanSignedOff, setHumanSignedOff] = useState(false);
  const [signOffTimestamp, setSignOffTimestamp] = useState<string | null>(null);
  const leadSignerName = "Dr. Julian Davies, MBChB MRCP";
  const [actions, setActions] = useState<ActionItem[]>(INITIAL_ACTION_ITEMS);
  const [checkedActions, setCheckedActions] = useState<Record<string, boolean>>({
    act1: false,
    act2: true,
    act3: false,
    act4: false,
  });
  const [isDossierModalOpen, setIsDossierModalOpen] = useState(false);

  const handleNavigateTab = (tab: ActiveTabType) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleHumanSignOff = () => {
    if (humanSignedOff) {
      setHumanSignedOff(false);
      setSignOffTimestamp(null);
      return;
    }
    setHumanSignedOff(true);
    setSignOffTimestamp(
      new Date().toLocaleTimeString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    );
  };

  const handleToggleAction = (id: string) => {
    setCheckedActions((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleResetActions = () => {
    setCheckedActions({ act1: false, act2: true, act3: false, act4: false });
  };

  const handleMarkAllResolved = () => {
    const allChecked: Record<string, boolean> = {};
    actions.forEach((act) => {
      allChecked[act.id] = true;
    });
    setCheckedActions(allChecked);
  };

  const handleAddAction = (item: Omit<ActionItem, "id">) => {
    const newId = `act_${Date.now()}`;
    setActions((prev) => [{ ...item, id: newId }, ...prev]);
    setCheckedActions((prev) => ({ ...prev, [newId]: false }));
  };

  const metrics = useMemo(() => {
    const activePatients = INITIAL_SYNTHETIC_PATIENTS.filter((p) => p.siteId !== "site-suffolk");
    const gatewayOffCount = activePatients.filter((p) => p.failsNothingGatewayOff).length;
    const gatewayOnCount = activePatients.filter((p) => p.failsNothingGatewayOn).length;
    return {
      gatewayOffCount,
      gatewayOnCount,
      currentCount: gatewayRuleOn ? gatewayOnCount : gatewayOffCount,
      deltaCount: gatewayOnCount - gatewayOffCount,
      totalSyntheticEvaluated: 304,
      abstainingCount: 64,
      participatingCount: 240,
    };
  }, [gatewayRuleOn]);

  const pendingActionsCount = actions.filter((a) => !checkedActions[a.id]).length;

  return (
    <div id="sponsorgrid-app" className="min-h-screen bg-slate-50 text-slate-900 antialiased flex flex-col overflow-x-hidden">
      <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-3 min-w-0">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 min-h-12 py-1.5">
            <button
              type="button"
              onClick={() => handleNavigateTab("feasibility_board")}
              className="flex items-center gap-2 shrink-0 min-w-0"
            >
              <span className="w-7 h-7 rounded-lg bg-sky-600 text-white flex items-center justify-center">
                <ShieldCheck className="w-4 h-4" />
              </span>
              <span className="font-bold text-sm tracking-tight">SponsorGrid</span>
            </button>

            <nav className="flex flex-1 items-center gap-0.5 min-w-0 overflow-x-auto">
              {TABS.map((tab) => {
                const active = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => handleNavigateTab(tab.id)}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold whitespace-nowrap ${
                      active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {tab.label}
                    {tab.id === "action_center" && pendingActionsCount > 0 ? (
                      <span className="ml-1 font-mono">{pendingActionsCount}</span>
                    ) : null}
                  </button>
                );
              })}
            </nav>

            <button
              type="button"
              onClick={handleHumanSignOff}
              className={`shrink-0 px-2.5 py-1 rounded-md text-xs font-semibold flex items-center gap-1 ${
                humanSignedOff ? "bg-emerald-600 text-white" : "bg-slate-900 text-white"
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {humanSignedOff ? "Signed off" : "Sign off"}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-3 py-5 min-w-0">
        {activeTab === "feasibility_board" && (
          <FeasibilityBoardView
            gatewayRuleOn={gatewayRuleOn}
            setGatewayRuleOn={setGatewayRuleOn}
            humanSignedOff={humanSignedOff}
            signOffTimestamp={signOffTimestamp}
            leadSignerName={leadSignerName}
            handleHumanSignOff={handleHumanSignOff}
            metrics={metrics}
            sites={SITES}
            patients={INITIAL_SYNTHETIC_PATIENTS}
            onNavigateTab={handleNavigateTab}
          />
        )}

        {activeTab === "ten_stage_pipeline" && (
          <PipelineView onNavigateTab={handleNavigateTab} leadSignerName={leadSignerName} />
        )}

        {activeTab === "modal_pydantic_agent" && (
          <ModalPydanticEngineView onNavigateTab={handleNavigateTab} />
        )}

        {activeTab === "action_center" && (
          <ActionCenterView
            actions={actions}
            checkedActions={checkedActions}
            onToggleAction={handleToggleAction}
            onResetActions={handleResetActions}
            onMarkAllResolved={handleMarkAllResolved}
            onAddAction={handleAddAction}
            sites={SITES}
            deltaCount={metrics.deltaCount}
            currentCount={metrics.currentCount}
            leadSignerName={leadSignerName}
            humanSignedOff={humanSignedOff}
            onOpenDossierModal={() => setIsDossierModalOpen(true)}
            onNavigateTab={handleNavigateTab}
          />
        )}

        {activeTab === "cohort_simulator" && (
          <CohortSimulatorView onNavigateTab={handleNavigateTab} />
        )}
      </main>

      <DossierModal
        isOpen={isDossierModalOpen}
        onClose={() => setIsDossierModalOpen(false)}
        leadSignerName={leadSignerName}
        humanSignedOff={humanSignedOff}
        signOffTimestamp={signOffTimestamp}
        actions={actions}
        checkedActions={checkedActions}
        sites={SITES}
        currentCandidatesCount={metrics.currentCount}
        deltaCount={metrics.deltaCount}
      />
    </div>
  );
}
