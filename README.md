# Aegntic Universal End-to-End Outcome Workflows

Model-agnostic and harness-agnostic execution framework for 5 end-to-end outcome workflows and a paired statistical evaluator.

Works natively across:
- **Google Antigravity / Gemini CLI**
- **Anthropic Claude Code / Claude Desktop**
- **Cursor / Windsurf / VS Code / Roo Code / Cline**
- **OpenClaw / Hermes / Local Agent Frameworks**
- **Terminal CLI / CI/CD Pipelines**

---

## The 5 Outcome Workflows

| Workflow | Native Invoke | Delivered Outcome | Compounding Asset |
| :--- | :--- | :--- | :--- |
| **Venture Lab** | `$venture-lab` | Tested offer or validation experiment with explicit missing evidence | Audience language, offer components, hypothesis outcomes |
| **Product Foundry** | `$product-foundry` | Working vertical slice with behavioral and regression evidence | Tested components, recovery procedures, regression cases |
| **Experience Studio** | `$experience-studio` | Implemented bespoke interface with interaction and accessibility evidence | Reusable interface patterns and usability regressions |
| **Knowledge Engine** | `$knowledge-engine` | Sourced decision plus reusable, versioned knowledge | Claim lineage, freshness rules, automated correction propagation |
| **Agent Evolution** | `$agent-evolution` | Tested workflow candidate and reversible promotion decision | Task bank, measured interventions, regression coverage |

---

## Universal CLI Runner (`aegntic`)

Installed globally at `~/.local/bin/aegntic` (on system `$PATH`):

```bash
# List all workflows, outcomes, and triggers
aegntic list

# Inspect full stage contracts and prompt specifications
aegntic inspect venture-lab
aegntic inspect product-foundry
aegntic inspect experience-studio
aegntic inspect knowledge-engine
aegntic inspect agent-evolution

# Run the paired results evaluator
aegntic eval --baseline base.json --candidate cand.json --contract contract.json

# Run unit tests across all evaluator suites (12/12 passing)
aegntic test

# Launch the universal MCP server over stdio
aegntic mcp

# Check system health and discovery symlinks
aegntic doctor
```

---

## Universal MCP Server (`aegntic-outcomes`)

Executable script: `/home/ae/plugins/bin/aegntic-outcomes-mcp.mjs`

### Exposed Tools
1. `venture_lab`: Market validation & offer testing.
2. `product_foundry`: Vertical slice implementation & regression freezing.
3. `experience_studio`: Bespoke avant-garde UI design & WCAG AAA verification.
4. `knowledge_engine`: Sourced decisions & claim DAG construction.
5. `agent_evolution`: Autonomous agent capability improvements & paired evaluation.
6. `paired_evaluator`: Exact binomial sign-test p-values & resource ceiling checks.

### Client Configurations

#### 1. Cursor (`.cursor/mcp.json`) & Windsurf
```json
{
  "mcpServers": {
    "aegntic-outcomes": {
      "command": "aegntic",
      "args": ["mcp"]
    }
  }
}
```

#### 2. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "aegntic-outcomes": {
      "command": "aegntic",
      "args": ["mcp"]
    }
  }
}
```

#### 3. Claude Code (`~/.claude.json`)
Registered under `mcpServers`:
```json
"aegntic-outcomes": {
  "type": "stdio",
  "command": "node",
  "args": ["/home/ae/plugins/bin/aegntic-outcomes-mcp.mjs"]
}
```

#### 4. Google Antigravity
Native tool schemas registered in `/home/ae/.gemini/antigravity/mcp/aegntic-outcomes/`.

#### 5. OpenClaw / Hermes / Universal Hub
Skills symlinked into `/home/ae/.agents/skills/`.
