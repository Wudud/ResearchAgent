# ResearchAgent Architecture

## Vision

ResearchAgent is an AI assistant designed to support the complete scientific research workflow.

The goal is not only to answer questions, but also to actively assist researchers in:

- Dataset construction
- Experiment management
- Meeting analysis
- Paper reading
- Knowledge management
- Code generation
- Project planning

---

## Overall Architecture

ResearchAgent

├── Core

├── Managers

├── Tools

├── Knowledge

├── Memory

├── Workflow

└── UI

## Core

The Core module is responsible for:

- Starting the system
- Loading configuration
- Scheduling tasks
- Managing all managers
- Calling tools
- Recording logs

## Managers

Managers are responsible for high-level scientific tasks.

Current managers:

- Dataset Manager
- Meeting Manager
- Experiment Manager
- Paper Manager
- Project Manager
- Knowledge Manager

## Tools

Tools are responsible for executing specific functions.

Examples:

- Open3D
- Whisper
- PDF Reader
- Excel
- Git
- Python

## Memory

Memory stores long-term research information.

Examples:

- Meeting history
- Experiment records
- Research ideas
- TODO list
- Teacher suggestions

## Knowledge

Knowledge stores external knowledge.

Examples:

- Papers
- Books
- Notes
- Dataset documents

## Workflow

Workflow controls the collaboration between different managers.

Examples:

Meeting Workflow

Recording

↓

Speech Recognition

↓

Meeting Summary

↓

Suggestion Analysis

↓

TODO Generation

↓

Project Update

## UI

The UI provides interaction for users.

Possible interfaces:

- Command Line
- Web UI
- Desktop Application