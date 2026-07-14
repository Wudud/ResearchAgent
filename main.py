"""ResearchAgent CLI — the main entry point for all operations.

Supports 9 subcommands:
  workflow paper|meeting|experiment|dataset|auto-index
  web
  agent run
  mcp-server
  health

Each subcommand delegates to src/cli/commands.py handlers.
"""
import argparse
import sys

from src.cli.commands import (
    cmd_workflow, cmd_web, cmd_agent, cmd_mcp_server, cmd_health, cmd_export,
    cmd_dataset_dedup, cmd_benchmark,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ResearchAgent — AI Research Assistant for DairySheepHR",
        prog="research-agent",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- workflow ----
    wf = sub.add_parser("workflow", help="Run a research workflow")
    wf_subs = wf.add_subparsers(dest="workflow_type", required=True)

    # workflow paper
    wp = wf_subs.add_parser("paper", help="Full paper ingestion pipeline")
    wp.add_argument("--file", required=True, help="Path to the paper file (PDF, etc.)")
    wp.add_argument("--no-index", action="store_true", help="Skip auto-indexing into knowledge base")
    wp.add_argument("--config", help="Path to config YAML")
    wp.set_defaults(func=cmd_workflow)

    # workflow meeting
    wm = wf_subs.add_parser("meeting", help="Full meeting analysis pipeline")
    wm.add_argument("--text", help="Meeting transcript text")
    wm.add_argument("--audio", help="Path to audio file for transcription")
    wm.add_argument("--title", help="Meeting title")
    wm.add_argument("--no-index", action="store_true")
    wm.add_argument("--config", help="Path to config YAML")
    wm.set_defaults(func=cmd_workflow)

    # workflow experiment
    we = wf_subs.add_parser("experiment", help="Full experiment lifecycle")
    we.add_argument("--name", required=True, help="Experiment name")
    we.add_argument("--dataset", default="", help="Dataset name")
    we.add_argument("--model", default="", help="Model name")
    we.add_argument("--params", default="{}", help="JSON parameters string")
    we.add_argument("--no-index", action="store_true")
    we.add_argument("--config", help="Path to config YAML")
    we.set_defaults(func=cmd_workflow)

    # workflow dataset
    wd = wf_subs.add_parser("dataset", help="Full dataset analysis pipeline")
    wd.add_argument("--root", help="Dataset root directory")
    wd.add_argument("--name", help="Dataset name")
    wd.add_argument("--no-index", action="store_true")
    wd.add_argument("--config", help="Path to config YAML")
    wd.set_defaults(func=cmd_workflow)

    # workflow auto-index
    wa = wf_subs.add_parser("auto-index", help="Batch index all items into knowledge base")
    wa.add_argument("--config", help="Path to config YAML")
    wa.set_defaults(func=cmd_workflow)

    # ---- web ----
    wb = sub.add_parser("web", help="Start the Streamlit Web UI")
    wb.add_argument("--config", help="Path to config YAML")
    wb.set_defaults(func=cmd_web)

    # ---- agent ----
    ag = sub.add_parser("agent", help="Run an autonomous agent")
    ag_subs = ag.add_subparsers(dest="agent_mode", required=True)
    run_ag = ag_subs.add_parser("run", help="Run agent with a goal")
    run_ag.add_argument("--type", required=True, choices=["paper", "meeting", "experiment", "dataset"],
                        help="Agent type")
    run_ag.add_argument("--goal", required=True, help="Goal description for the agent")
    run_ag.add_argument("--config", help="Path to config YAML")
    run_ag.set_defaults(func=cmd_agent)

    # ---- mcp-server ----
    mc = sub.add_parser("mcp-server", help="Start as MCP stdio server")
    mc.add_argument("--config", help="Path to config YAML")
    mc.set_defaults(func=cmd_mcp_server)

    # ---- health ----
    hl = sub.add_parser("health", help="Run system health checks")
    hl.add_argument("--config", help="Path to config YAML")
    hl.set_defaults(func=cmd_health)

    # ---- export ----
    ex = sub.add_parser("export", help="Export paper-ready outputs")
    ex.add_argument("--type", required=True, choices=["experiment", "dataset"], help="Export type")
    ex.add_argument("--format", required=True, choices=["latex", "markdown", "csv", "excel", "plot"], help="Output format")
    ex.add_argument("--root", help="Dataset root directory (for type=dataset)")
    ex.add_argument("--output", help="Output file path")
    ex.add_argument("--config", help="Path to config YAML")
    ex.set_defaults(func=cmd_export)

    # ---- dataset ----
    ds = sub.add_parser("dataset", help="Dataset operations")
    ds_subs = ds.add_subparsers(dest="dataset_action", required=True)
    ds_dedup = ds_subs.add_parser("dedup", help="Detect duplicate point clouds")
    ds_dedup.add_argument("--root", required=True, help="Dataset root directory")
    ds_dedup.add_argument("--voxel-size", type=float, default=0.05)
    ds_dedup.add_argument("--threshold", type=float, default=0.01)
    ds_dedup.add_argument("--output", help="Output report path")
    ds_dedup.set_defaults(func=cmd_dataset_dedup)

    # ---- benchmark ----
    bm = sub.add_parser("benchmark", help="Run system performance benchmark")
    bm.add_argument("--config", help="Path to config YAML")
    bm.set_defaults(func=cmd_benchmark)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
