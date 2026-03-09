# You Need an Advisor MCP

**Your AI-powered YNAB budgeting advisor**

You Need an Advisor MCP is more than an API wrapper. It connects AI assistants like Claude to your [YNAB](https://www.ynab.com/) budget with embedded knowledge of YNAB's budgeting methodology -- so you get advice grounded in both your real data and proven budgeting principles.

```bash
uvx --from you-need-an-advisor-mcp ynaa-mcp
```

---

## What makes this different

Most YNAB integrations give you raw data. You Need an Advisor MCP gives you a **budgeting advisor** that understands the Four Rules, knows how to handle overspending, and can walk you through a debt payoff plan -- all while pulling live numbers from your budget.

---

## Features

<div class="grid cards" markdown>

- :material-chat-processing-outline: **Natural Language Budgeting**

  ***

  Ask about your budget in plain English. "How much did I spend on dining out last month?" Just ask -- the server handles the API calls.

- :material-book-open-variant: **YNAB Methodology Built-In**

  ***

  Embedded knowledge of YNAB's Four Rules, overspending strategies, credit card management, reconciliation, and Age of Money. Advice that follows the method.

- :material-api: **Complete API Coverage**

  ***

  Every YNAB endpoint accessible: budgets, accounts, categories, transactions, payees, months, and scheduled transactions. 8 tool domains, 30+ actions.

- :material-chart-line: **Analysis & Insights**

  ***

  Budget health checks, spending trend analysis, savings tracking, income vs. expense breakdowns, and category deep dives. 6 analysis prompts ready to use.

- :material-map-marker-path: **Workflow Guides**

  ***

  Step-by-step guided processes for debt payoff planning, new budget setup, financial reviews, and more. 6 workflow guides built in.

- :material-shield-lock-outline: **Secure & Private**

  ***

  Your Personal Access Token stays on your machine. No data is stored, forwarded, or logged by the server. All communication stays between your client and YNAB's API.

</div>

---

## Quick start

**1. Get a YNAB Personal Access Token** from [YNAB Developer Settings](https://app.ynab.com/settings/developer)

**2. Add to Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ynab": {
      "command": "uvx",
      "args": ["--from", "you-need-an-advisor-mcp", "ynaa-mcp"],
      "env": {
        "YNAB_PAT": "your-token-here"
      }
    }
  }
}
```

**3. Ask a question:**

> "How much did I spend on groceries this month?"

That's it. The server handles authentication, rate limiting, budget resolution, and data formatting.

---

## Learn more

- **[Installation](getting-started/installation.md)** -- Prerequisites and setup options
- **[Quickstart](getting-started/quickstart.md)** -- Connect your first AI assistant
- **[User Guide](user-guide/tools/index.md)** -- Tools, prompts, and resources
- **[Contributing](contributing/index.md)** -- Development setup and PR workflow
