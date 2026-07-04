# Lab 2.2: Connecting the Ecosystem - MCP Servers & Built-in Claude Code Tools

## Overview
This lab demonstrates how to connect Claude Code to multiple MCP (Model Context Protocol) servers and use built-in tools (Glob, Grep, Read, Edit, Write) for efficient, incremental codebase exploration and refactoring.

**Scenario**: NorthPeak Outfitters outdoor-gear store with two independent data sources:
- **Orders service**: Live order data (status, items, tracking)
- **Documentation**: Customer-facing policies (shipping, returns, warranty)

## Lab Structure

```
Lab 2.2/
├── .mcp.json                     # MCP server configuration
├── requirements.txt              # Python dependencies (mcp>=1.2.0)
├── mcp_servers/                  # MCP server implementations
│   ├── orders_server.py         # Orders data source
│   └── docs_server.py           # Policy documents source
├── data/                        # Data files
│   ├── orders.json              # Sample order records
│   └── docs/                    # Policy documents
│       ├── returns-policy.md
│       ├── shipping-policy.md
│       └── warranty.md
└── sample_codebase/             # TypeScript project for refactoring
    ├── src/
    │   ├── analytics.ts         # Analytics helpers (with deprecated function)
    │   ├── notifications.ts     # Notification functions
    │   └── orders.ts            # Order processing functions
    ├── tests/
    │   ├── notifications.test.ts
    │   └── orders.test.ts
    └── MIGRATION.md             # Migration documentation

```

## Exercise 1: MCP Server Integration (S4)

### Objective
Connect two MCP servers to provide Claude Code with real-time access to multiple data sources without copy-pasting data.

### MCP Servers Configured

**northpeak-orders** - Order data source
- `get_order(order_id)`: Retrieve single order by ID
- `find_orders_by_email(email)`: Find all orders for a customer

**northpeak-docs** - Policy documentation source  
- `list_docs()`: List all policy document names
- `read_doc(name)`: Read full text of a policy document
- `search_docs(query)`: Search documents by query with snippets

### Key Concepts
- **Multiple independent sources**: Each MCP server provides a distinct data domain
- **Declarative configuration**: Servers defined once in `.mcp.json`, available throughout session
- **No data duplication**: Agent calls tools on-demand instead of loading everything upfront

### Example Multi-Source Query
*"Order NP-100190 was delivered. The customer wants to return one item — are they still inside the return window, and what condition rules apply?"*

This requires:
1. Order status from `northpeak-orders.get_order()`
2. Return policy from `northpeak-docs.read_doc("returns-policy")`
3. Combined analysis considering both sources

## Exercise 2: Precise Refactoring with Built-in Tools (S5)

### Objective
Migrate a deprecated analytics function using precise, scriptable tool actions instead of loading the entire repository.

### Task
Migrate `logEvent(name, payload)` → `track({ name, props })` across the codebase.

### Tool Workflow

1. **Glob** - Find files by pattern
   ```
   Glob for all *.test.ts files under sample_codebase
   ```
   Result: Map project structure (2 test files found)

2. **Grep** - Search file contents
   ```
   Grep for `logEvent(` in sample_codebase/src
   ```
   Result: 4 call sites across 2 files + deprecated definition

3. **Read** - Open only needed files
   ```
   Read sample_codebase/src/analytics.ts
   ```
   Result: Understand `track({ name, props })` signature

4. **Edit** - Minimal, targeted changes
   - Updated `src/notifications.ts`: 2 call sites + import
   - Updated `src/orders.ts`: 2 call sites + import
   - Changes: Function name + parameter structure + import statement

5. **Write** - Create new documentation
   ```
   Write sample_codebase/MIGRATION.md
   ```
   Result: Document migration for future reference

### Before → After

**Before (Deprecated):**
```typescript
import { logEvent } from "./analytics";
logEvent("order_shipped_email", { orderId, email });
```

**After (Migrated):**
```typescript
import { track } from "./analytics";
track({ name: "order_shipped_email", props: { orderId, email } });
```

## Exercise 3: Incremental Exploration (S5)

### Objective
Make a one-line change by locating precisely, reading narrowly, and changing minimally.

### Task
Rename analytics event: `order_cancelled` → `order_canceled` (one L for standardization)

### Efficient Path
1. **Grep** for `order_cancelled` → Found 1 call site in `src/orders.ts`
2. **Read** only that file
3. **Edit** just that line: Changed event name string
4. **Update** MIGRATION.md to document the change

### Cost Comparison
- **Efficient approach**: Touch exactly 1 file, read ~10 lines
- **Heavy approach**: Read all files first, then change → Same result, much higher context cost

## Key Learning Outcomes

### 1. MCP Servers Give Real Context
- **Benefit**: Agent has access to live, structured data sources
- **Alternative**: Manually paste data into chat (goes stale, bloats context)
- **Result**: Answers combine multiple sources accurately

### 2. Built-in Tools Enable Precise Actions
- **Glob**: Pattern-based file discovery
- **Grep**: Exact symbol/string location
- **Read**: Targeted file reading
- **Edit**: Minimal in-place changes
- **Write**: New file creation
- **Result**: Scriptable, repeatable, efficient operations

### 3. Incremental Exploration Beats "Load Everything"
- **Find → Read-only-what-matters → Change** loop
- Lower context usage, faster execution, higher accuracy
- Scales to large codebases where loading everything is impossible

### 4. Tools + Context Reinforce Each Other
- **Good sources without precise tools**: Agent has data but acts inefficiently
- **Precise tools without sources**: Agent acts efficiently but on guesses
- **Both together**: Fast, cheap, accurate agent behavior

## Setup Requirements

### Prerequisites
- Python 3.10+
- Claude Code CLI
- Virtual environment for MCP servers

### Installation
```bash
cd "Lab 2.2"
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Verification
```bash
claude
# Inside Claude Code:
/mcp
# Should show both northpeak-orders and northpeak-docs as connected
```

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Server not connected after `/mcp` | Python interpreter doesn't have `mcp` package | Point `.mcp.json` command to venv interpreter |
| Import error after migration | Changed function call but not import | Edit includes import statement changes |
| Missed call sites during Grep | Incomplete search pattern | Use Grep before Edit to locate all occurrences |

## Reflection Questions

1. **Why declare MCP servers vs. pasting data?**
   - Declared sources remain fresh across session
   - No context bloat from redundant data
   - Agent calls tools as needed

2. **Why Glob → Grep → Read → Edit order?**
   - Progressively narrow focus from project structure to specific lines
   - Only load what's needed for the change
   - Verify exhaustively before changing

3. **When is "read whole file" the right call?**
   - When the change requires understanding entire file context
   - When multiple unrelated changes span the file
   - When file is small and change scope unclear

4. **What breaks if you have good sources but no tool discipline?**
   - Context waste from over-reading
   - Slower execution from loading unnecessary files
   - Higher token costs for same result

5. **What breaks if you have tool discipline but no sources?**
   - Agent invents answers instead of retrieving facts
   - Cannot combine cross-domain information
   - Inaccurate responses despite efficient actions

## Files Summary

| File | Purpose | Section |
|------|---------|---------|
| `.mcp.json` | MCP server configuration | S4 |
| `mcp_servers/orders_server.py` | Orders data source | S4 |
| `mcp_servers/docs_server.py` | Docs data source | S4 |
| `data/orders.json` | Sample order records | S4 |
| `data/docs/*.md` | Policy documents | S4 |
| `sample_codebase/src/analytics.ts` | Analytics with deprecated function | S5 |
| `sample_codebase/src/notifications.ts` | Notification functions (migrated) | S5 |
| `sample_codebase/src/orders.ts` | Order functions (migrated) | S5 |
| `sample_codebase/MIGRATION.md` | Migration documentation | S5 |

## Further Reading

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/overview)
- [Model Context Protocol](https://modelcontextprotocol.io)
- Lab 2.1: Designing Reliable Tools (prerequisite)

---

**Lab completed**: All exercises implemented, migrations documented in MIGRATION.md
