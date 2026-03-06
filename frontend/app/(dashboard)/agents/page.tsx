'use client';

import { useState } from 'react';
import Header from '@/components/layout/Header';
import { agentsApi, type AgentResult } from '@/lib/api';
import IntegrationGate from '@/components/IntegrationGate';
import { useSetupStatus } from '@/lib/useSetupStatus';

type AgentId = 'build_captain' | 'ui_surgeon' | 'test_pilot' | 'data_curator' | 'ops_boss';

interface AgentConfig {
  id: AgentId;
  name: string;
  icon: string;
  tagline: string;
  description: string;
  inputLabel: string;
  placeholder: string;
  outputSections: { key: string; label: string }[];
  run: (input: string) => Promise<AgentResult>;
}

const AGENTS: AgentConfig[] = [
  {
    id: 'build_captain',
    name: 'Build Captain',
    icon: '🏗️',
    tagline: 'Build planner',
    description: 'Turns your goal into a tight build plan, breaks it into tickets, sets acceptance criteria, and keeps changes coherent across routes/components/state.',
    inputLabel: 'Build request or goal',
    placeholder: 'e.g. Build Library filters + persistence + saved crates',
    outputSections: [
      { key: 'assumptions', label: 'Assumptions' },
      { key: 'task_list', label: 'Task List' },
      { key: 'file_level_plan', label: 'File-Level Plan' },
      { key: 'acceptance_criteria', label: 'Acceptance Criteria' },
      { key: 'verification_steps', label: 'Verification Steps' },
    ],
    run: (input) => agentsApi.runBuildCaptain(input),
  },
  {
    id: 'ui_surgeon',
    name: 'UI Surgeon',
    icon: '🎨',
    tagline: 'Screenshot → Components',
    description: 'Takes a screenshot, reference HTML, or UI description and outputs component breakdown, Tailwind tokens, shadcn mapping, and build order.',
    inputLabel: 'UI description or reference',
    placeholder: 'e.g. A dashboard with a sidebar nav, content grid, data table with filters and a status pill column',
    outputSections: [
      { key: 'layout_anatomy', label: 'Layout Anatomy' },
      { key: 'component_inventory', label: 'Component Inventory' },
      { key: 'tailwind_tokens', label: 'Tailwind Tokens' },
      { key: 'shadcn_components', label: 'shadcn Components' },
      { key: 'responsive_rules', label: 'Responsive Rules' },
      { key: 'file_structure', label: 'File Structure' },
      { key: 'build_order', label: 'Build Order' },
    ],
    run: (input) => agentsApi.runUiSurgeon(input),
  },
  {
    id: 'test_pilot',
    name: 'Test Pilot',
    icon: '🧪',
    tagline: 'QA + Playwright',
    description: 'Generates test cases, edge cases, and Playwright scripts, then helps debug failures with minimal fixes.',
    inputLabel: 'Feature or user flow to test',
    placeholder: 'e.g. Library filters must persist across sessions and not break on mobile',
    outputSections: [
      { key: 'risk_list', label: 'Risk List' },
      { key: 'manual_checklist', label: 'Manual Test Checklist' },
      { key: 'playwright_test_plan', label: 'Playwright Test Plan' },
      { key: 'playwright_scripts', label: 'Playwright Scripts' },
      { key: 'data_fixtures', label: 'Data Fixtures' },
      { key: 'failure_triage', label: 'Failure Triage' },
    ],
    run: (input) => agentsApi.runTestPilot(input),
  },
  {
    id: 'data_curator',
    name: 'Data Curator',
    icon: '📊',
    tagline: 'Valuation + Confidence',
    description: 'Designs the valuation pipeline (comps, match scoring, outliers) with clear data contracts and sanity checks.',
    inputLabel: 'Valuation or data pipeline context',
    placeholder: 'e.g. Add comps table + confidence pill logic for vinyl record valuations',
    outputSections: [
      { key: 'data_model', label: 'Data Model' },
      { key: 'scoring_rules', label: 'Scoring Rules' },
      { key: 'required_inputs', label: 'Required Inputs' },
      { key: 'api_shapes', label: 'API Shapes' },
      { key: 'validation_rules', label: 'Validation + Logging' },
      { key: 'verification_queries', label: 'Verification Queries' },
    ],
    run: (input) => agentsApi.runDataCurator(input),
  },
  {
    id: 'ops_boss',
    name: 'Ops Boss',
    icon: '⚙️',
    tagline: 'CI + Environments',
    description: 'Makes your build repeatable: env vars, secrets, CI checks, dependency hygiene, and release basics.',
    inputLabel: 'Deployment or CI/CD context',
    placeholder: 'e.g. Lock down ImgBB key server-side + add CI checks for lint, typecheck, and tests',
    outputSections: [
      { key: 'env_var_matrix', label: 'Env Var Matrix' },
      { key: 'secrets_handling', label: 'Secrets Handling' },
      { key: 'ci_pipeline_steps', label: 'CI Pipeline Steps' },
      { key: 'caching_strategy', label: 'Caching Strategy' },
      { key: 'security_basics', label: 'Security Basics' },
      { key: 'deploy_checklist', label: 'Deploy Checklist' },
    ],
    run: (input) => agentsApi.runOpsBoss(input),
  },
];

function renderValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((v) => (typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v))).join('\n');
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value ?? '');
}

export default function AgentsPage() {
  const { isConfigured } = useSetupStatus();
  const grokConfigured = isConfigured('grok_ai');
  const [activeAgent, setActiveAgent] = useState<AgentId>('build_captain');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const agent = AGENTS.find((a) => a.id === activeAgent)!;

  function handleSelectAgent(id: AgentId) {
    setActiveAgent(id);
    setInput('');
    setResult(null);
    setError(null);
  }

  async function handleRun() {
    if (!input.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await agent.run(input.trim());
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Agent request failed');
    } finally {
      setLoading(false);
    }
  }

  const confidence = result?.result?.confidence as number | undefined;

  return (
    <>
      <Header title="Specialist Agents" />
      <div className="p-6 space-y-6">

        {/* Agent selector */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              onClick={() => handleSelectAgent(a.id)}
              className={`flex flex-col items-start gap-1 p-4 rounded-xl border transition-all text-left card-hover ${
                activeAgent === a.id
                  ? 'bg-primary/10 border-primary/50 text-primary'
                  : 'bg-surface border-border-subtle text-text-muted hover:bg-white/5 hover:text-text-main'
              }`}
            >
              <span className="text-2xl">{a.icon}</span>
              <p className="text-sm font-semibold leading-tight">{a.name}</p>
              <p className="text-xs opacity-70">{a.tagline}</p>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Agent brief + input */}
          <div className="space-y-4">
            <div className="bg-surface border border-border-subtle rounded-xl p-5">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-3xl">{agent.icon}</span>
                <div>
                  <h2 className="text-text-main font-semibold">{agent.name}</h2>
                  <p className="text-primary text-xs font-mono">{agent.tagline}</p>
                </div>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">{agent.description}</p>
            </div>

            <div className="bg-surface border border-border-subtle rounded-xl p-5 space-y-3">
              <label className="block text-primary font-mono text-xs uppercase tracking-widest">
                {agent.inputLabel}
              </label>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={agent.placeholder}
                rows={6}
                className="w-full bg-background border border-border-subtle rounded-lg px-3 py-2 text-text-main text-sm placeholder:text-text-faint focus:outline-none focus:border-primary/50 resize-none font-mono"
              />
              <IntegrationGate feature="grok_ai" isConfigured={grokConfigured}>
                <button
                  onClick={handleRun}
                  disabled={loading || !input.trim()}
                  className="w-full py-2.5 bg-primary/10 hover:bg-primary/20 text-primary text-sm font-mono rounded-lg border border-primary/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? `Running ${agent.name}…` : `Run ${agent.name} →`}
                </button>
              </IntegrationGate>
              {error && (
                <p className="text-error text-xs font-mono bg-error/10 border border-error/30 rounded px-3 py-2">
                  {error}
                </p>
              )}
            </div>
          </div>

          {/* Output panel */}
          <div className="bg-surface border border-border-subtle rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-primary font-mono text-xs uppercase tracking-widest">Output</h2>
              {confidence !== undefined && (
                <span className={`text-xs font-mono px-2 py-0.5 rounded border ${
                  confidence >= 0.7
                    ? 'bg-success/10 text-success border-success/30'
                    : confidence >= 0.4
                    ? 'bg-warning/10 text-warning border-warning/30'
                    : 'bg-error/10 text-error border-error/30'
                }`}>
                  Confidence {Math.round(confidence * 100)}%
                </span>
              )}
            </div>

            {loading && (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-16 bg-background rounded-lg animate-pulse" />
                ))}
              </div>
            )}

            {!loading && !result && !error && (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <span className="text-4xl mb-3 opacity-40">{agent.icon}</span>
                <p className="text-text-faint text-sm">Enter your request and run the agent to see the output here.</p>
              </div>
            )}

            {!loading && result && (
              <div className="space-y-4 overflow-y-auto max-h-[600px] pr-1">
                {agent.outputSections.map(({ key, label }) => {
                  const val = result.result[key];
                  if (val === undefined || val === null) return null;
                  const text = renderValue(val);
                  if (!text) return null;
                  return (
                    <div key={key} className="bg-background border border-border-subtle rounded-lg p-3">
                      <p className="text-primary text-xs font-mono uppercase tracking-wider mb-2">{label}</p>
                      <pre className="text-text-main text-xs whitespace-pre-wrap break-words font-mono leading-relaxed">
                        {text}
                      </pre>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

      </div>
    </>
  );
}
