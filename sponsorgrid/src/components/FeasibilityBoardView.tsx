import React, { useState } from "react";
import { CheckCircle2, Search, XCircle } from "lucide-react";
import { ActiveTabType, SiteFeasibility, SyntheticPatient } from "../types";

interface FeasibilityBoardViewProps {
  gatewayRuleOn: boolean;
  setGatewayRuleOn: (on: boolean) => void;
  humanSignedOff: boolean;
  signOffTimestamp: string | null;
  leadSignerName: string;
  handleHumanSignOff: () => void;
  metrics: {
    gatewayOffCount: number;
    gatewayOnCount: number;
    currentCount: number;
    deltaCount: number;
    totalSyntheticEvaluated: number;
    abstainingCount: number;
    participatingCount: number;
  };
  sites: SiteFeasibility[];
  patients: SyntheticPatient[];
  onNavigateTab: (tab: ActiveTabType) => void;
}

export const FeasibilityBoardView: React.FC<FeasibilityBoardViewProps> = ({
  gatewayRuleOn,
  setGatewayRuleOn,
  humanSignedOff,
  signOffTimestamp,
  leadSignerName,
  handleHumanSignOff,
  metrics,
  sites,
  patients,
  onNavigateTab,
}) => {
  const [selectedSiteFilter, setSelectedSiteFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<SyntheticPatient | null>(null);

  const displayedPatients = patients.filter((patient) => {
    if (selectedSiteFilter !== "all" && patient.siteId !== selectedSiteFilter) return false;
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    const fact = gatewayRuleOn ? patient.missingFactGatewayOn : patient.missingFactGatewayOff;
    return (
      patient.id.toLowerCase().includes(query) ||
      (patient.pseudonym || "").toLowerCase().includes(query) ||
      patient.siteName.toLowerCase().includes(query) ||
      (fact || "").toLowerCase().includes(query)
    );
  });

  return (
    <div id="feasibility-board-view" className="space-y-4 min-w-0">
      <div className="bg-white rounded-xl border border-slate-200 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-base font-bold text-slate-900">One fact away</h2>
          <p className="text-xs text-slate-500">SG-ONC-302 · 2 of 3 sites</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs font-semibold ${gatewayRuleOn ? "text-slate-400" : "text-amber-700"}`}>
            Off
          </span>
          <button
            id="gateway-rule-toggle-button"
            type="button"
            role="switch"
            aria-checked={gatewayRuleOn}
            aria-label="Gateway rule"
            onClick={() => setGatewayRuleOn(!gatewayRuleOn)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full ${
              gatewayRuleOn ? "bg-sky-600" : "bg-amber-600"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                gatewayRuleOn ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
          <span className={`text-xs font-semibold ${gatewayRuleOn ? "text-sky-700" : "text-slate-400"}`}>
            On
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Metric label="1 fact away" value={metrics.currentCount} hint={`${metrics.gatewayOffCount} off`} />
        <Metric label="Sites" value="2 / 3" hint="West Suffolk hold" />
        <div className="p-3 rounded-xl bg-white border border-slate-200 min-w-0">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Sign-off</div>
          <div className="text-lg font-bold text-slate-900 truncate">
            {humanSignedOff ? "Signed" : "Pending"}
          </div>
          <div className="text-[11px] text-slate-500 truncate">
            {humanSignedOff ? signOffTimestamp : leadSignerName.split(",")[0]}
          </div>
          <button
            type="button"
            onClick={handleHumanSignOff}
            className="mt-1 text-xs font-semibold text-sky-700"
          >
            {humanSignedOff ? "Revoke" : "Sign"}
          </button>
        </div>
        <div className="p-3 rounded-xl bg-white border border-slate-200 min-w-0">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Actions</div>
          <div className="text-lg font-bold text-slate-900">4</div>
          <button
            type="button"
            onClick={() => onNavigateTab("action_center")}
            className="mt-2 text-xs font-semibold text-sky-700"
          >
            Open
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {sites.map((site) => (
          <div
            key={site.id}
            className={`p-3 rounded-xl border min-w-0 ${
              site.abstaining ? "bg-slate-50 border-dashed border-slate-300" : "bg-white border-slate-200"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-sm font-bold text-slate-900 truncate">{site.name}</h3>
              <span
                className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full shrink-0 ${
                  site.abstaining ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"
                }`}
              >
                {site.abstaining ? "Hold" : "Live"}
              </span>
            </div>
            <div className="mt-2 text-xl font-bold text-slate-900">
              {site.abstaining ? "—" : site.gatewayOnCandidates}
            </div>
            <p className="text-xs text-slate-600 mt-1 line-clamp-2">{site.primaryBlocker}</p>
            <button
              type="button"
              onClick={() => {
                if (site.abstaining) {
                  onNavigateTab("action_center");
                  return;
                }
                setSelectedSiteFilter(site.id);
                document.getElementById("full-ledger-section")?.scrollIntoView({ behavior: "smooth" });
              }}
              className="mt-2 text-xs font-semibold text-sky-700"
            >
              {site.abstaining ? "Resolve" : "Filter"}
            </button>
          </div>
        ))}
      </div>

      <div id="full-ledger-section" className="bg-white rounded-xl border border-slate-200 overflow-hidden min-w-0">
        <div className="p-3 border-b border-slate-100 flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-bold text-slate-900 mr-auto">Ledger</h3>
          <select
            id="site-filter-select"
            value={selectedSiteFilter}
            onChange={(e) => setSelectedSiteFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-xs rounded-lg px-2 py-1.5"
          >
            <option value="all">All sites</option>
            <option value="site-cambridge">Addenbrooke's</option>
            <option value="site-papworth">Papworth</option>
            <option value="site-suffolk">West Suffolk</option>
          </select>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2 pointer-events-none" />
            <input
              id="ledger-search-input"
              type="text"
              placeholder="Search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-xs rounded-lg pl-7 pr-2 py-1.5 w-36"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase tracking-wider text-[10px]">
                <th className="py-2 px-3">Candidate</th>
                <th className="py-2 px-3">Site</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Missing fact</th>
                <th className="py-2 px-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {displayedPatients.map((patient) => {
                const isFailsNothing = gatewayRuleOn
                  ? patient.failsNothingGatewayOn
                  : patient.failsNothingGatewayOff;
                const missingFact = gatewayRuleOn
                  ? patient.missingFactGatewayOn
                  : patient.missingFactGatewayOff;
                return (
                  <tr key={patient.id} className="hover:bg-slate-50">
                    <td className="py-2 px-3">
                      <div className="font-semibold text-slate-900">{patient.pseudonym || "Candidate"}</div>
                      <div className="font-mono text-[10px] text-slate-400">{patient.id}</div>
                    </td>
                    <td className="py-2 px-3 text-slate-700">{patient.siteName}</td>
                    <td className="py-2 px-3">
                      {patient.siteId === "site-suffolk" ? (
                        <span className="text-slate-500">Hold</span>
                      ) : isFailsNothing ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                          <CheckCircle2 className="w-3 h-3" />
                          1 fact
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-600 font-medium">
                          <XCircle className="w-3 h-3" />
                          {gatewayRuleOn ? "Out" : "Fail"}
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-slate-800">{missingFact || "—"}</td>
                    <td className="py-2 px-3 text-right">
                      <button
                        type="button"
                        onClick={() => setSelectedPatient(patient)}
                        className="px-2 py-1 rounded-md bg-slate-100 text-slate-800 font-semibold"
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selectedPatient && (
        <div
          id="patient-fact-inspector-modal"
          className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4"
        >
          <div className="bg-white border border-slate-200 rounded-xl max-w-md w-full p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="font-bold text-sm text-slate-900 truncate">
                  {selectedPatient.pseudonym} · {selectedPatient.id}
                </h3>
                <p className="text-xs text-slate-500">{selectedPatient.siteName}</p>
              </div>
              <button type="button" onClick={() => setSelectedPatient(null)} className="text-slate-400 text-sm">
                ✕
              </button>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-[10px] uppercase font-bold text-sky-700">Missing fact</div>
              <div className="text-sm font-bold text-slate-900">
                {gatewayRuleOn
                  ? selectedPatient.missingFactGatewayOn || "Multiple exclusions"
                  : selectedPatient.missingFactGatewayOff || "Failed off-rule"}
              </div>
            </div>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <Stat k="ECOG" v={String(selectedPatient.ecog)} />
              <Stat k="EGFR" v={String(selectedPatient.egfrExon20)} />
              <Stat k="CrCl" v={String(selectedPatient.creatinineClearance)} />
              <Stat k="Plt" v={String(selectedPatient.platelets)} />
            </div>
            <div className="flex justify-between items-center pt-1">
              <button
                type="button"
                onClick={() => {
                  setSelectedPatient(null);
                  onNavigateTab("action_center");
                }}
                className="text-xs font-semibold text-sky-700"
              >
                Actions
              </button>
              <button
                type="button"
                onClick={() => setSelectedPatient(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function Metric({ label, value, hint }: { label: string; value: React.ReactNode; hint: string }) {
  return (
    <div className="p-3 rounded-xl bg-white border border-slate-200 min-w-0">
      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
      <div className="text-[11px] text-slate-500">{hint}</div>
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="p-2 bg-slate-50 rounded-lg border border-slate-200">
      <span className="text-[10px] uppercase font-bold text-slate-400 block">{k}</span>
      <span className="font-mono font-bold text-slate-800">{v}</span>
    </div>
  );
}
