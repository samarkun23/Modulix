# Modulix

> An AI-powered autonomous software engineering platform that aims to plan, build, execute, test, and manage software projects through an isolated execution environment.

<sub>🚧 **PROJECT UNDER DEVELOPMENT** — This project is actively being developed. Features, architecture, and implementation details are subject to change.</sub>

## Overview

Autonomous Engineer is an experimental AI software engineering platform designed to automate parts of the software development lifecycle.

The goal is to build an AI agent capable of understanding software requirements, planning implementation steps, generating code, executing commands, debugging errors, and managing project workflows.

Rather than simply generating code snippets, the platform aims to provide an environment where AI agents can interact with real project files and development tools.

## Vision

Build an autonomous engineering system that can:

- Understand natural language software requirements.
- Break complex requirements into actionable tasks.
- Design implementation plans and project structures.
- Generate and modify source code.
- Execute commands in isolated environments.
- Detect errors and attempt automated debugging.
- Run tests and evaluate generated implementations.
- Work with local repositories and GitHub.
- Request human approval before sensitive operations.

## Core Architecture

The system follows a modular architecture with clear separation between orchestration, execution, workspace management, and AI reasoning.

### 1. Execution Engine

Responsible for providing isolated environments where AI-generated code and commands can execute.

Technologies:
- Docker
- Python
- Docker SDK

### 2. Runtime Abstraction

Provides a common interface between the execution engine and higher-level components.

This abstraction is intended to allow different runtime implementations without coupling the entire application to Docker.

### 3. Workspace Management

Responsible for:
- Creating isolated project workspaces.
- Managing project files and directories.
- Reading and writing source files.
- Tracking workspace lifecycle.
- Maintaining project data independently of container lifecycle.

### 4. Command Execution

Responsible for executing commands inside isolated environments and collecting:

- Standard output
- Standard error
- Exit codes
- Execution duration
- Timeout and termination information

### 5. AI Model Gateway

A unified layer for interacting with different AI models.

The planned architecture supports a hybrid model strategy, allowing different models to handle different engineering tasks.

### 6. Planning and Orchestration

Responsible for coordinating the engineering workflow:

1. Requirement understanding.
2. Task decomposition.
3. Implementation planning.
4. Code generation.
5. Execution.
6. Testing and evaluation.
7. Error analysis and debugging.

### 7. Persistence and Recovery

PostgreSQL will be used to persist important application metadata, including tasks, workspaces, and container references.

The system will also implement recovery mechanisms to reconcile application state with Docker container state after restarts.

### 8. GitHub Integration

Planned capabilities include:

- Repository access.
- Code changes.
- Branch management.
- Git diffs.
- Human-approved commits and pull requests.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python |
| API Layer | FastAPI (planned) |
| Container Runtime | Docker |
| Database | PostgreSQL |
| AI Integration | Hybrid AI Models |
| Version Control | Git / GitHub |
| Frontend | Planned |
| Testing | Pytest |
| Monitoring | Planned |

## Development Status

| Component | Status |
|---|---|
| Runtime abstraction | Initial implementation |
| Docker Manager | Implemented |
| Docker Manager tests | Written |
| Workspace Manager | Pending |
| Command Executor | Pending |
| PostgreSQL persistence | Pending |
| Recovery Manager | Pending |
| AI Model Gateway | Planned |
| Task Planner | Planned |
| Code Generation Engine | Planned |
| Evaluation and Debugging | Planned |
| GitHub Integration | Planned |
| Frontend | Planned |

## Design Principles

- **Modularity:** Independent components with well-defined responsibilities.
- **Isolation:** Execute generated code inside controlled environments.
- **Persistence:** Important application state must survive restarts.
- **Recoverability:** Support recovery from execution and infrastructure failures.
- **Human Oversight:** Sensitive operations should require explicit approval.
- **Extensibility:** Support different models and runtime implementations.
- **Observability:** Maintain execution logs and useful diagnostics.

## Project Structure

The repository structure is evolving as development progresses.

```text
autonomous-engineer/
│
├── interfaces/
│   └── runtime.py
│
├── docker/
│   └── manager.py
│
├── workspace/
│   └── manager.py
│
├── executor/
│   └── runner.py
│
├── database/
│   └── models.py
│
├── tests/
│
├── main.py
│
├── requirements.txt
│
└── README.md
```

## Current Development Focus

The current development phase focuses on building the foundational execution infrastructure.

The immediate priorities are:

1. Docker lifecycle management.
2. Workspace isolation and filesystem operations.
3. Secure command execution.
4. Persistent application state.
5. Runtime recovery.

AI planning, code generation, and orchestration will be integrated after the execution foundation is established.

## Security Considerations

Security is a core architectural concern.

The planned system will incorporate:

- Container resource limits.
- Restricted container capabilities.
- Filesystem isolation.
- Command execution timeouts.
- Network access restrictions.
- Controlled image selection.
- Human approval for sensitive operations.

Docker containers alone are not considered a complete security boundary. Additional isolation and security hardening will be required before production deployment.

## Disclaimer

This project is an independent experimental engineering project.

It is currently under active development and is not production-ready. Some features described above represent architectural goals rather than completed functionality.

## License

License to be determined.
