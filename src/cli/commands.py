import json
import sys

from src.core.agent import ResearchAgent

def _create_agent(config_path: str = None, quiet: bool = False) -> ResearchAgent:
    """Factory: creates and initializes a ResearchAgent instance.

    Args:
        config_path: Path to YAML config file, or None for default.
        quiet: If True, suppress banner and "System Ready" output.
               Required for MCP stdio mode — any extra stdout corrupts JSON-RPC.
    """
    agent = ResearchAgent(config_path=config_path)
    agent.initialize(quiet=quiet)
    return agent

def cmd_workflow(args):
    """Dispatch workflow subcommands to the appropriate workflow class."""

    workflows = agent.workflows
    auto_index = not getattr(args, 'no_index', False)

    if args.workflow_type == "paper":
        wf = workflows["paper"]
        result = wf.run(file_path=args.file, auto_index=auto_index)
        print(json.dumps({"status": result["status"]}, ensure_ascii=False))

    elif args.workflow_type == "meeting":
        wf = workflows["meeting"]
        if args.text:
            result = wf.run(text=args.text, title=args.title, auto_index=auto_index)
        elif args.audio:
            result = wf.run(audio_path=args.audio, title=args.title, auto_index=auto_index)
        else:
            print("Error: either --text or --audio is required for meeting workflow")
            sys.exit(1)
        print(json.dumps({"status": result["status"]}, ensure_ascii=False))

    elif args.workflow_type == "experiment":
        wf = workflows["experiment"]
        params = json.loads(args.params) if args.params else {}
        result = wf.run(
            name=args.name, dataset=args.dataset, model=args.model,
            parameters=params, auto_index=auto_index,
        )
        print(json.dumps({"status": result["status"]}, ensure_ascii=False))

    elif args.workflow_type == "dataset":
        wf = workflows["dataset"]
        result = wf.run(root_path=args.root, dataset_name=args.name, auto_index=auto_index)
        print(json.dumps({"status": result["status"]}, ensure_ascii=False))

    elif args.workflow_type == "auto-index":
        wf = workflows["auto_index"]
        result = wf.run()
        print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_web(args):
    """Start the Streamlit Web UI."""
    from pathlib import Path
    import subprocess

    app_path = Path(__file__).parent.parent / "web" / "app.py"
    print(f"Starting ResearchAgent Web UI...")
    print(f"App: {app_path}\n")

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    import os
    if hasattr(args, 'config') and args.config:
        os.environ["RESEARCHAGENT_CONFIG"] = args.config
    subprocess.run(cmd)

def cmd_mcp_server(args):
    """Start the MCP server in stdio mode.

    Uses quiet=True to suppress all print output — the MCP protocol
    communicates over stdio via JSON-RPC, and any extraneous output
    would corrupt the channel.
    """
    agent = _create_agent(args.config, quiet=True)
    from src.mcp.server import run_mcp_server
    run_mcp_server(agent)

def cmd_export(args):
    """Export paper-ready outputs: latex, markdown, csv, excel, or plots."""
    from src.export.latex_exporter import LatexExporter
    from src.export.markdown_exporter import MarkdownExporter
    from src.export.csv_exporter import CsvExporter
    from src.export.excel_exporter import ExcelExporter
    from src.export.plot_exporter import PlotExporter
    from src.dataset.scanner import DatasetScanner
    from src.dataset.statistics import StatisticsGenerator

    fmt = args.format
    export_type = args.type

    if export_type == "dataset":
        root = args.root or "."
        scanner = DatasetScanner()
        inventory = scanner.scan(root)
        stats_gen = StatisticsGenerator()
        stats = stats_gen.generate(inventory)

        stats_dict = {
            "Total Files": stats.total_files,
            "Total Size": stats.total_size_human,
            "Point Cloud Files": stats.point_cloud_files,
            "PLY Files": stats.ply_files,
            "PCD Files": stats.pcd_files,
            "Avg Point Count": stats.avg_point_count or "N/A",
            "Min Point Count": stats.min_point_count or "N/A",
            "Max Point Count": stats.max_point_count or "N/A",
        }
        ext_info = {f"Ext: {k}": v for k, v in stats.extensions.items()}
        stats_dict.update(ext_info)

        if fmt == "latex":
            exporter = LatexExporter()
            output = exporter.export_dataset_stats(stats_dict)
        elif fmt == "markdown":
            exporter = MarkdownExporter()
            output = exporter.export_dataset_stats(stats_dict)
        elif fmt == "csv":
            rows = [{"Statistic": k, "Value": v} for k, v in stats_dict.items()]
            exporter = CsvExporter()
            output = exporter.export_metrics(rows)
        elif fmt == "plot":
            exporter = PlotExporter()
            output_path = args.output or "workspace/reports/dataset_stats.png"
            output = exporter.dataset_stats_figure(stats.extensions, output_path)
        else:
            print(f"Unsupported format for dataset: {fmt}")
            sys.exit(1)
        print(output)

    elif export_type == "experiment":
        agent = _create_agent(args.config)
        repo = agent.services.get("experiment_repo")
        if repo is None:
            print("Error: experiment_repo not available")
            sys.exit(1)
        experiments = repo.list_all()
        exp_dicts = [
            {
                "name": e.name,
                "dataset": e.dataset,
                "model": e.model,
                "status": e.status,
                "parameters": str(e.parameters),
            }
            for e in experiments
        ]

        if fmt == "latex":
            exporter = LatexExporter()
            output = exporter.export_experiment_table(exp_dicts)
        elif fmt == "markdown":
            exporter = MarkdownExporter()
            output = exporter.export_experiment(exp_dicts)

            exporter = CsvExporter()
            output = exporter.export_experiments(exp_dicts)
        elif fmt == "excel":
            exporter = ExcelExporter()
            output_path = args.output or "workspace/reports/experiments.xlsx"
            output = exporter.export({"Experiments": exp_dicts}, output_path)
        else:
            print(f"Unsupported format for experiment: {fmt}")
            sys.exit(1)
        print(output)

    else:
        print(f"Unknown export type: {export_type}. Supported: dataset, experiment")

def cmd_dataset_dedup(args):
    """Detect duplicate point clouds in a dataset directory."""
    from src.dataset.dedup import PointCloudDedupChecker

    checker = PointCloudDedupChecker(
        voxel_size=args.voxel_size,
        chamfer_threshold=args.threshold,
    )
    result = checker.check_directory(args.root)
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    report = checker.generate_report(result, output_path=args.output)
    print(report)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_benchmark(args):
    """Run system performance benchmark."""
    from src.benchmark.runner import BenchmarkRunner
    agent = _create_agent(args.config)
    runner = BenchmarkRunner(agent)
    results = runner.run()
    print(runner.report(results))
    print(json.dumps(results, ensure_ascii=False, indent=2))

def cmd_health(args):
    """Run health checks and print status."""
    agent = _create_agent(args.config)
    from src.health.checker import HealthChecker
    checker = HealthChecker(agent)
    result = checker.check_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
