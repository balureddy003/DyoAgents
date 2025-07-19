# 🧠 Dyogents

**Dyogents** is an open-source platform for building, orchestrating, and deploying intelligent agents powered by LLMs. Designed for real-world enterprise workflows, Dyogents lets you compose domain-specific agents into collaborative teams—integrated with your existing systems, governed with precision, and extensible by design.

> “Composable AI agents working together like your smartest team.”

---

## 🚀 What is Dyogents?

Dyogents turns agents into first-class citizens:
- 🤖 Modular agents ("pods") with tools, memory, and decision logic
- 🔌 Integrate with real systems like SAP, Salesforce, Kafka, OPC-UA, etc.
- 🔁 Coordinate agents via chat, task DAGs, or collaborative workflows
- 🧠 Use any LLM: OpenAI, Claude, Ollama, HuggingFace, and more
- 🛡 Track, trace, and govern with audit logs and cost budgets

---

## 🔧 Platform Highlights

### 🧱 Agent Pods
- Domain-specific agents for ERP, MES, RAG, IoT, finance, and more
- YAML-based definitions with LLM + toolchains + memory

### ⚙️ Dyogents Grid (Runtime)
- Task routing, context sharing, memory, and fallback logic

### 🛍 Dyogents Hub (Marketplace)
- Discover, publish, and reuse agents and prebuilt workflows

### 🎨 Dyogents Studio (Visual Builder)
- Drag-and-drop canvas for designing agent pipelines
- Ideal for domain experts and low-code builders

### 🔌 Dyogents Mesh (Integrations)
- Native support for REST, SAP, Kafka, Salesforce, MongoDB, OPC-UA

### 🔐 Dyogents Observe (Governance)
- Full observability: tracing, RBAC, cost tracking, tool audits

---

## 🧠 Why Dyogents?

| Problem                     | Dyogents Solution                              |
|----------------------------|-------------------------------------------------|
| Shadow AI projects         | Central governance via Dyogents Observe        |
| Vendor lock-in             | Bring your own LLM, deploy anywhere             |
| Siloed agents              | Coordinate via Grid and Mesh                   |
| Hard-to-integrate systems  | Use Mesh for plug-and-play integrations        |

---

## 📦 Quickstart

```bash
git clone https://github.com/dyogents/dyogents.git
cd dyogents
pip install -r requirements.txt
dyogents init --template planner-agent
```

---

## 📚 Documentation

📘 Powered by Docusaurus  
➡️ [https://docs.dyogents.dev](https://docs.dyogents.dev)

Includes:
- Agent Spec (DyoSpec)
- Visual Studio Walkthrough
- Integration Examples
- Runtime API Docs
- Contribution Guide

---

## 🛠 Tech Stack

- Python 3.10+
- FastAPI + AsyncIO
- MongoDB or PostgreSQL
- OpenAI / Claude / Ollama / HuggingFace
- Kafka, SAP, Salesforce, REST, OPC-UA

---

## 👥 Contributing

We welcome contributions:
- Agent templates and bundles
- System connectors and plugins
- Visual Studio UI components

See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## 📄 License

MIT License © 2025 [Dyogents Foundation](https://dyogents.org)
