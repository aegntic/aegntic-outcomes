#!/usr/bin/env node

/**
 * Aegntic Outcome Workflows Universal MCP Server
 * Exposes the 5 End-to-End Outcome Workflows and the Paired Results Evaluator
 * over standard JSON-RPC 2.0 stdio transport.
 * 
 * Works with: Claude Desktop, Cursor, Windsurf, Roo Code, VS Code, Zed,
 * OpenCode, LibreChat, and any standard Model Context Protocol client.
 */

import readline from "node:readline";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const SERVER_NAME = "aegntic-outcomes-mcp";
const SERVER_VERSION = "1.0.0";
const PLUGINS_DIR = "/home/ae/plugins";

const WORKFLOWS = {
  venture_lab: {
    name: "venture_lab",
    description: "Venture Lab ($venture-lab): Market validation workflow. Formulates tested commercial offers or ready-to-run validation experiments with an explicit missing evidence audit.",
    skillPath: `${PLUGINS_DIR}/aegntic-venture-lab/skills/venture-lab/SKILL.md`,
    inputSchema: {
      type: "object",
      properties: {
        objective: { type: "string", description: "The core commercial concept, product thesis, or domain opportunity." },
        target_audience: { type: "string", description: "Target customer ICP, persona, or buyer profile." },
        constraints: { type: "array", items: { type: "string" }, description: "Budget, technical, or regulatory constraints." },
        stage: { type: "string", enum: ["all", "01_audience", "02_offer", "03_experiment", "04_audit"], default: "all", description: "Specific stage to execute or plan." }
      },
      required: ["objective"]
    }
  },
  product_foundry: {
    name: "product_foundry",
    description: "Product Foundry ($product-foundry): Software execution workflow. Delivers a working vertical slice with behavioral proof and permanent regression cases.",
    skillPath: `${PLUGINS_DIR}/aegntic-product-foundry/skills/product-foundry/SKILL.md`,
    inputSchema: {
      type: "object",
      properties: {
        objective: { type: "string", description: "The feature, user journey, or endpoint to implement as a vertical slice." },
        repository_path: { type: "string", description: "Target repository or workspace directory." },
        constraints: { type: "array", items: { type: "string" }, description: "Tech stack, performance, or library constraints." },
        stage: { type: "string", enum: ["all", "01_boundary", "02_implementation", "03_behavioral", "04_regression"], default: "all" }
      },
      required: ["objective"]
    }
  },
  experience_studio: {
    name: "experience_studio",
    description: "Experience Studio ($experience-studio): User interface & interaction design workflow. Delivers implemented bespoke interfaces with interaction and accessibility evidence.",
    skillPath: `${PLUGINS_DIR}/aegntic-experience-studio/skills/experience-studio/SKILL.md`,
    inputSchema: {
      type: "object",
      properties: {
        objective: { type: "string", description: "Interface, view, component, or layout to design and implement." },
        aesthetic_direction: {
          type: "string",
          enum: ["technical_precision", "brutalist_minimalism", "organic_warmth", "neo_noir", "experimental_motion"],
          description: "Distinctive avant-garde aesthetic direction (rejects generic AI templates)."
        },
        target_component: { type: "string", description: "Component path or target view file." },
        stage: { type: "string", enum: ["all", "01_architecture", "02_microinteractions", "03_wcag_audit", "04_evidence"], default: "all" }
      },
      required: ["objective"]
    }
  },
  knowledge_engine: {
    name: "knowledge_engine",
    description: "Knowledge Engine ($knowledge-engine): Evidence-based decision workflow. Delivers sourced decisions, claim lineage, freshness decay rules, and automated correction propagation.",
    skillPath: `${PLUGINS_DIR}/aegntic-knowledge-engine/skills/knowledge-engine/SKILL.md`,
    inputSchema: {
      type: "object",
      properties: {
        objective: { type: "string", description: "The strategic, technical, or operational question to resolve." },
        primary_sources: { type: "array", items: { type: "string" }, description: "Primary URLs, documents, commit SHAs, or benchmark reports to ground the decision." },
        freshness_half_life_days: { type: "number", description: "Days before evidence decays and triggers re-validation." },
        stage: { type: "string", enum: ["all", "01_claims", "02_dag", "03_freshness", "04_memo"], default: "all" }
      },
      required: ["objective"]
    }
  },
  agent_evolution: {
    name: "agent_evolution",
    description: "Agent Evolution ($agent-evolution): Autonomous capability improvement workflow. Delivers tested workflow candidates and reversible promotion decisions via paired evaluations.",
    skillPath: `${PLUGINS_DIR}/aegntic-agent-evolution/skills/agent-evolution/SKILL.md`,
    inputSchema: {
      type: "object",
      properties: {
        target_workflow: { type: "string", description: "Name or path of the agent workflow, skill, or prompt to improve." },
        intervention_hypothesis: { type: "string", description: "The specific intervention expected to produce statistical gain." },
        task_bank_path: { type: "string", description: "Path to benchmark task bank JSON." },
        stage: { type: "string", enum: ["all", "01_harvest", "02_intervention", "03_evaluation", "04_promotion"], default: "all" }
      },
      required: ["target_workflow", "intervention_hypothesis"]
    }
  },
  paired_evaluator: {
    name: "paired_evaluator",
    description: "Paired Results Evaluator: Evaluates baseline vs candidate task runs using exact sign-test binomial statistics and resource ceiling verification.",
    inputSchema: {
      type: "object",
      properties: {
        baseline_tasks: {
          type: "array",
          items: {
            type: "object",
            properties: { id: { type: "string" }, score: { type: "number" }, evidence: { type: "string" } },
            required: ["id", "score", "evidence"]
          },
          description: "List of baseline run tasks with score and evidence."
        },
        candidate_tasks: {
          type: "array",
          items: {
            type: "object",
            properties: {
              id: { type: "string" },
              score: { type: "number" },
              evidence: { type: "string" },
              latency_ms: { type: "number" },
              tokens: { type: "number" },
              critical_failure: { type: "boolean" },
              failure_reason: { type: "string" }
            },
            required: ["id", "score", "evidence"]
          },
          description: "List of candidate run tasks to compare."
        },
        contract: {
          type: "object",
          properties: {
            required_tasks: { type: "array", items: { type: "string" } },
            max_latency_ms: { type: "number" },
            max_tokens: { type: "number" },
            practical_threshold: { type: "number" }
          },
          description: "Optional constraints and practical significance threshold."
        }
      },
      required: ["baseline_tasks", "candidate_tasks"]
    }
  }
};

function readSkillDoc(skillPath) {
  try {
    return fs.readFileSync(skillPath, "utf8");
  } catch (err) {
    return `Error reading skill at ${skillPath}: ${err.message}`;
  }
}

function handleToolCall(name, args) {
  if (name === "paired_evaluator") {
    const evaluatorPath = `${PLUGINS_DIR}/aegntic-agent-evolution/evaluator/evaluator.py`;
    const tmpBase = `/tmp/_mcp_base_${Date.now()}.json`;
    const tmpCand = `/tmp/_mcp_cand_${Date.now()}.json`;
    const tmpContract = `/tmp/_mcp_contract_${Date.now()}.json`;

    try {
      fs.writeFileSync(tmpBase, JSON.stringify(args.baseline_tasks || []));
      fs.writeFileSync(tmpCand, JSON.stringify(args.candidate_tasks || []));
      fs.writeFileSync(tmpContract, JSON.stringify(args.contract || {}));

      const out = execFileSync("python3", [evaluatorPath, "--baseline", tmpBase, "--candidate", tmpCand, "--contract", tmpContract], { encoding: "utf8" });
      return { content: [{ type: "text", text: out }] };
    } catch (err) {
      return { isError: true, content: [{ type: "text", text: `Evaluation execution error: ${err.message}` }] };
    } finally {
      try { fs.unlinkSync(tmpBase); } catch {}
      try { fs.unlinkSync(tmpCand); } catch {}
      try { fs.unlinkSync(tmpContract); } catch {}
    }
  }

  const wf = WORKFLOWS[name];
  if (!wf) {
    return { isError: true, content: [{ type: "text", text: `Unknown tool: ${name}` }] };
  }

  const doc = readSkillDoc(wf.skillPath);
  const responsePlan = {
    workflow: name,
    objective: args.objective || args.target_workflow,
    selected_stage: args.stage || "all",
    instructions: doc,
    parameters: args,
    next_step: `Follow the 4-stage execution sequence outlined in the skill instructions. Produce each stage's exit artifacts deterministically.`
  };

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(responsePlan, null, 2)
      }
    ]
  };
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on("line", (line) => {
  if (!line.trim()) return;
  let request;
  try {
    request = JSON.parse(line);
  } catch (err) {
    const errorResponse = {
      jsonrpc: "2.0",
      id: null,
      error: { code: -32700, message: "Parse error", data: String(err) }
    };
    process.stdout.write(JSON.stringify(errorResponse) + "\n");
    return;
  }

  const { id, method, params } = request;

  if (method === "initialize") {
    const response = {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: SERVER_NAME, version: SERVER_VERSION }
      }
    };
    process.stdout.write(JSON.stringify(response) + "\n");
    return;
  }

  if (method === "notifications/initialized") {
    return;
  }

  if (method === "tools/list") {
    const toolList = Object.values(WORKFLOWS).map((w) => ({
      name: w.name,
      description: w.description,
      inputSchema: w.inputSchema
    }));

    const response = {
      jsonrpc: "2.0",
      id,
      result: { tools: toolList }
    };
    process.stdout.write(JSON.stringify(response) + "\n");
    return;
  }

  if (method === "tools/call") {
    const toolName = params?.name;
    const toolArgs = params?.arguments || {};
    const toolResult = handleToolCall(toolName, toolArgs);

    const response = {
      jsonrpc: "2.0",
      id,
      result: toolResult
    };
    process.stdout.write(JSON.stringify(response) + "\n");
    return;
  }

  if (method === "ping") {
    process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id, result: {} }) + "\n");
    return;
  }

  const errorResponse = {
    jsonrpc: "2.0",
    id,
    error: { code: -32601, message: `Method not found: ${method}` }
  };
  process.stdout.write(JSON.stringify(errorResponse) + "\n");
});
