from dataclasses import dataclass, field

@dataclass
class FileEntry:
    relative_path: str
    absolute_path: str
    size_bytes: int
    extension: str
    md5_hex: str | None = None

@dataclass
class DatasetInventory:
    root_path: str
    files: list[FileEntry] = field(default_factory=list)
    total_files: int = 0
    total_size_bytes: int = 0
    extension_counts: dict[str, int] = field(default_factory=dict)

@dataclass
class IntegrityIssue:
    severity: str  # "error" | "warning"
    file_path: str
    message: str

@dataclass
class IntegrityReport:
    passed: bool = True
    issues: list[IntegrityIssue] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    checksum_mismatches: list[str] = field(default_factory=list)

@dataclass
class DatasetStats:
    total_files: int = 0
    total_size_human: str = ""
    extensions: dict[str, int] = field(default_factory=dict)
    point_cloud_files: int = 0
    ply_files: int = 0
    pcd_files: int = 0
    avg_point_count: float | None = None
    min_point_count: int | None = None
    max_point_count: int | None = None
    subdirectories: list[str] = field(default_factory=list)
