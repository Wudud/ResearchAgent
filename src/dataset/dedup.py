import hashlib
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

class PointCloudDedupChecker:
    def __init__(self, voxel_size: float = 0.05, chamfer_threshold: float = 0.01):
        self._voxel_size = voxel_size
        self._chamfer_threshold = chamfer_threshold
        self._logger = logging.getLogger("ResearchAgent.PointCloudDedup")

    def check_directory(self, root: str) -> dict:
        root_path = Path(root)
        if not root_path.exists():
            return {"error": f"Directory not found: {root}"}

        pc_files = sorted(
            p for p in root_path.rglob("*")
            if p.suffix.lower() in (".ply", ".pcd", ".pts", ".xyz")
        )
        if not pc_files:
            return {"error": "No point cloud files found", "total_files": 0}

        file_paths = [str(p) for p in pc_files]

        md5_hashes, md5_groups = self._md5_dedup(file_paths)
        voxel_hashes = {}
        for fp in file_paths:
            try:
                vh = self._voxel_hash(fp)
                if vh is not None:
                    voxel_hashes[fp] = vh
            except Exception as e:
                self._logger.warning(f"Voxel hash failed for {fp}: {e}")

        pairs = self._find_near_duplicates(file_paths, voxel_hashes, md5_groups)

        return {
            "total_files": len(file_paths),
            "unique_files": len(md5_groups),
            "exact_duplicates": sum(len(g) - 1 for g in md5_groups.values()),
            "near_duplicate_pairs": len(pairs),
            "md5_groups": {h: [str(Path(p).name) for p in g] for h, g in md5_groups.items() if len(g) > 1},
            "near_duplicates": [
                {"file_a": str(Path(a).name), "file_b": str(Path(b).name), "chamfer_distance": round(d, 6)}
                for a, b, d in pairs
            ],
        }

    def generate_report(self, result: dict, output_path: str = None) -> str:
        lines = [
            "# Point Cloud Deduplication Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Voxel Size**: {self._voxel_size}",
            f"**Chamfer Threshold**: {self._chamfer_threshold}",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Files | {result.get('total_files', 0)} |",
            f"| Unique Files | {result.get('unique_files', 0)} |",
            f"| Exact Duplicates | {result.get('exact_duplicates', 0)} |",
            f"| Near-Duplicate Pairs | {result.get('near_duplicate_pairs', 0)} |",
            "",
        ]

        md5_groups = result.get("md5_groups", {})
        if md5_groups:
            lines.append("## Exact Duplicates (MD5)")
            lines.append("")
            for h, files in md5_groups.items():
                lines.append(f"- **Hash**: `{h[:12]}...`")
                for f in files:
                    lines.append(f"  - `{f}`")
                lines.append("")

        pairs = result.get("near_duplicates", [])
        if pairs:
            lines.append("## Near Duplicates (Chamfer Distance)")
            lines.append("")
            lines.append("| File A | File B | Chamfer Distance |")
            lines.append("|--------|--------|------------------|")
            for p in pairs:
                lines.append(f"| `{p['file_a']}` | `{p['file_b']}` | {p['chamfer_distance']} |")
            lines.append("")

        report = "\n".join(lines)
        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8")
            self._logger.info(f"Dedup report saved to: {path}")

        return report

    def _md5_dedup(self, file_paths: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
        hashes = {}
        groups: dict[str, list[str]] = {}
        for fp in file_paths:
            try:
                with open(fp, "rb") as f:
                    h = hashlib.md5(f.read()).hexdigest()
            except Exception as e:
                self._logger.warning(f"MD5 failed for {fp}: {e}")
                h = f"error:{fp}"
            hashes[fp] = h
            groups.setdefault(h, []).append(fp)
        return hashes, groups

    def _voxel_hash(self, file_path: str) -> str | None:
        points = self._load_points(file_path)
        if points is None or len(points) == 0:
            return None
        voxel_indices = (points[:, :3] / self._voxel_size).astype(np.int32)
        unique_voxels = np.unique(voxel_indices, axis=0)
        return hashlib.md5(unique_voxels.tobytes()).hexdigest()

    def _find_near_duplicates(
        self, file_paths: list[str], voxel_hashes: dict[str, str], md5_groups: dict[str, list[str]]
    ) -> list[tuple[str, str, float]]:
        representatives = {}
        for h, group in md5_groups.items():
            representatives[group[0]] = h

        candidates = sorted(representatives.keys())
        pairs = []
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                a, b = candidates[i], candidates[j]
                vh_a = voxel_hashes.get(a)
                vh_b = voxel_hashes.get(b)
                if vh_a and vh_b and vh_a == vh_b:
                    d = self._chamfer_distance(a, b)
                    if d is not None and d < self._chamfer_threshold:
                        pairs.append((a, b, d))
        return pairs

    def _chamfer_distance(self, file_a: str, file_b: str) -> float | None:
        pts_a = self._load_points(file_a)
        pts_b = self._load_points(file_b)
        if pts_a is None or pts_b is None:
            return None

        try:
            from scipy.spatial import cKDTree
        except ImportError:
            return self._chamfer_brute(pts_a, pts_b)

        tree_b = cKDTree(pts_b[:, :3])
        dist_a, _ = tree_b.query(pts_a[:, :3], k=1)
        tree_a = cKDTree(pts_a[:, :3])
        dist_b, _ = tree_a.query(pts_b[:, :3], k=1)
        return float(np.mean(dist_a) + np.mean(dist_b))

    def _chamfer_brute(self, pts_a: np.ndarray, pts_b: np.ndarray) -> float:
        diff_ab = pts_a[:, None, :3] - pts_b[None, :, :3]
        dist_ab = np.linalg.norm(diff_ab, axis=2)
        dist_a = np.min(dist_ab, axis=1)
        dist_b = np.min(dist_ab, axis=0)
        return float(np.mean(dist_a) + np.mean(dist_b))

    def _load_points(self, file_path: str) -> np.ndarray | None:
        suffix = Path(file_path).suffix.lower()
        try:
            if suffix == ".ply":
                return self._load_ply(file_path)
            elif suffix == ".pcd":
                return self._load_pcd(file_path)
            elif suffix in (".pts", ".xyz"):
                return np.loadtxt(file_path, comments="#")
            else:
                return self._load_with_open3d(file_path)
        except Exception as e:
            self._logger.warning(f"Failed to load {file_path}: {e}")
            return self._load_with_open3d(file_path)

    def _load_ply(self, file_path: str) -> np.ndarray | None:
        with open(file_path, "rb") as f:
            header = []
            while True:
                line = f.readline()
                if not line:
                    return None
                header.append(line.decode("utf-8", errors="replace").strip())
                if header[-1] == "end_header":
                    break
                if len(header) > 2000:
                    return None

            vertex_count = 0
            fmt = "ascii"
            for h in header:
                if h.startswith("element vertex "):
                    vertex_count = int(h.split()[-1])
                elif h == "format binary_little_endian 1.0":
                    fmt = "binary"
                elif h == "format ascii 1.0":
                    fmt = "ascii"

            if vertex_count == 0:
                return None

            xyz_dtype = np.dtype([("x", "f4"), ("y", "f4"), ("z", "f4")])
            if fmt == "binary":
                data_size = vertex_count * xyz_dtype.itemsize
                raw = f.read(data_size)
                if len(raw) < data_size:
                    return None
                arr = np.frombuffer(raw, dtype=xyz_dtype)
            else:
                data = f.read().decode("utf-8", errors="replace")
                arr = np.fromstring(data, sep=" ", count=vertex_count * 3).reshape(vertex_count, 3)
                arr = np.rec.fromarrays([arr[:, 0], arr[:, 1], arr[:, 2]], dtype=xyz_dtype)

            return np.column_stack([arr["x"], arr["y"], arr["z"]])

    def _load_pcd(self, file_path: str) -> np.ndarray | None:
        with open(file_path, "rb") as f:
            header = []
            while True:
                line = f.readline()
                if not line:
                    return None
                h = line.decode("utf-8", errors="replace").strip()
                header.append(h)
                if h.startswith("DATA"):
                    break
                if len(header) > 500:
                    return None

        vertex_count = 0
        data_type = "ascii"
        for h in header:
            if h.startswith("POINTS "):
                vertex_count = int(h.split()[-1])
            elif h.startswith("DATA "):
                data_type = h.split()[-1]

        if vertex_count == 0:
            return None

        if data_type == "ascii":
            data = f.read().decode("utf-8", errors="replace")
            arr = np.fromstring(data, sep=" ", count=vertex_count * 3).reshape(vertex_count, 3)
            return arr
        else:
            raw = f.read(vertex_count * 4 * 3)
            return np.frombuffer(raw, dtype=np.float32).reshape(vertex_count, 3)

    def _load_with_open3d(self, file_path: str) -> np.ndarray | None:
        try:
            import open3d as o3d
            pcd = o3d.io.read_point_cloud(file_path)
            return np.asarray(pcd.points)
        except Exception:
            return None
