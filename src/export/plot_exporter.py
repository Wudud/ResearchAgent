import logging
from pathlib import Path

class PlotExporter:
    def __init__(self):
        self._logger = logging.getLogger("ResearchAgent.PlotExporter")

    def confusion_matrix(self, cm: list[list[int]], labels: list[str], output_path: str, title: str = "Confusion Matrix") -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(cm, cmap="Blues", aspect="auto")

        for i in range(len(cm)):
            for j in range(len(cm[0])):
                ax.text(j, i, str(cm[i][j]), ha="center", va="center", fontsize=10)

        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(title)
        fig.colorbar(im, ax=ax)

        return self._save_figure(fig, output_path)

    def loss_curve(self, train_loss: list[float], val_loss: list[float] | None, output_path: str, title: str = "Loss Curve") -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 4))
        epochs = range(1, len(train_loss) + 1)
        ax.plot(epochs, train_loss, "b-", label="Train Loss")
        if val_loss:
            ax.plot(epochs, val_loss, "r--", label="Val Loss")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return self._save_figure(fig, output_path)

    def iou_bar(self, categories: list[str], iou_values: list[float], output_path: str, title: str = "IoU by Category") -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(max(6, len(categories) * 0.6), 4))
        colors = plt.cm.viridis([i / len(categories) for i in range(len(categories))])
        bars = ax.bar(categories, iou_values, color=colors)
        ax.set_ylabel("IoU")
        ax.set_title(title)
        ax.set_ylim(0, 1.05)

        for bar, val in zip(bars, iou_values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9)

        return self._save_figure(fig, output_path)

    def dataset_stats_figure(self, extension_counts: dict[str, int], output_path: str, title: str = "Dataset File Distribution") -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 4))
        labels = list(extension_counts.keys())
        values = list(extension_counts.values())
        colors = plt.cm.Set2([i / max(1, len(labels)) for i in range(len(labels))])
        ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140)
        ax.set_title(title)

        return self._save_figure(fig, output_path)

    def _save_figure(self, fig, output_path: str) -> str:
        import matplotlib.pyplot as plt

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(path), dpi=300, bbox_inches="tight")
        plt.close(fig)
        self._logger.info(f"Plot exported to: {path}")
        return str(path)
