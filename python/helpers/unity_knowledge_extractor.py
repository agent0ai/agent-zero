"""
Unity Knowledge Extraction System.

Automatically parses and indexes Unity projects into Qdrant for intelligent retrieval:
- C# scripts with class/method analysis
- Scene files with GameObject hierarchies
- Prefabs and asset metadata
- Project settings and configuration
- Build logs and error history
"""

import asyncio
import hashlib
import os
import re
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from python.helpers.unity_qdrant_enhanced import (
    UnityQdrantEnhanced, UnityCollectionType, UnityQueryContext
)

logger = logging.getLogger(__name__)


class UnityFileType(Enum):
    """Unity file types for extraction."""
    SCENE = ".unity"
    PREFAB = ".prefab"
    SCRIPT = ".cs"
    ASSET = ".asset"
    META = ".meta"
    MATERIAL = ".mat"
    ANIMATION = ".anim"
    ANIMATOR = ".controller"
    SHADER = ".shader"
    COMPUTE_SHADER = ".compute"
    SCRIPTABLE_OBJECT = ".asset"


@dataclass
class ExtractionProgress:
    """Track extraction progress."""
    total_files: int = 0
    processed_files: int = 0
    scripts_extracted: int = 0
    scenes_extracted: int = 0
    assets_extracted: int = 0
    prefabs_extracted: int = 0
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class CSharpClass:
    """Parsed C# class information."""
    name: str
    namespace: Optional[str]
    base_classes: List[str]
    interfaces: List[str]
    attributes: List[str]
    fields: List[Dict[str, Any]]
    properties: List[Dict[str, Any]]
    methods: List[Dict[str, Any]]
    is_abstract: bool = False
    is_partial: bool = False
    is_static: bool = False


@dataclass
class UnityGameObject:
    """Parsed Unity GameObject from scene/prefab."""
    name: str
    file_id: str
    tag: str
    layer: int
    is_active: bool
    components: List[Dict[str, Any]]
    children_ids: List[str]
    parent_id: Optional[str]
    transform: Optional[Dict[str, Any]]


class UnityKnowledgeExtractor:
    """
    Extracts and indexes Unity project knowledge into Qdrant.

    Features:
    - Deep C# script analysis (classes, methods, fields, Unity callbacks)
    - Scene/Prefab hierarchy parsing with component data
    - Asset dependency tracking
    - Incremental updates (only re-index changed files)
    - Parallel processing for large projects
    """

    # Unity lifecycle methods for special indexing
    UNITY_CALLBACKS = {
        "Awake", "Start", "OnEnable", "OnDisable", "OnDestroy",
        "Update", "FixedUpdate", "LateUpdate",
        "OnCollisionEnter", "OnCollisionExit", "OnCollisionStay",
        "OnCollisionEnter2D", "OnCollisionExit2D", "OnCollisionStay2D",
        "OnTriggerEnter", "OnTriggerExit", "OnTriggerStay",
        "OnTriggerEnter2D", "OnTriggerExit2D", "OnTriggerStay2D",
        "OnMouseDown", "OnMouseUp", "OnMouseEnter", "OnMouseExit",
        "OnBecameVisible", "OnBecameInvisible",
        "OnGUI", "OnDrawGizmos", "OnDrawGizmosSelected",
        "OnValidate", "Reset", "OnApplicationQuit", "OnApplicationPause",
        "OnAnimatorIK", "OnAnimatorMove",
        "OnNetworkSpawn", "OnNetworkDespawn",  # Netcode
    }

    # Common Unity base classes
    UNITY_BASE_CLASSES = {
        "MonoBehaviour", "ScriptableObject", "Editor", "EditorWindow",
        "NetworkBehaviour", "StateMachineBehaviour", "PropertyDrawer"
    }

    def __init__(
        self,
        qdrant_client: UnityQdrantEnhanced,
        project_id: str,
        max_workers: int = 4,
        batch_size: int = 50
    ):
        self.qdrant = qdrant_client
        self.project_id = project_id
        self.max_workers = max_workers
        self.batch_size = batch_size

        # Index tracking for incremental updates
        self._file_hashes: Dict[str, str] = {}
        self._extraction_progress = ExtractionProgress()

    async def extract_project(
        self,
        project_path: str,
        incremental: bool = True,
        progress_callback: Optional[callable] = None
    ) -> ExtractionProgress:
        """
        Extract entire Unity project knowledge.

        Args:
            project_path: Path to Unity project root
            incremental: Only re-index changed files
            progress_callback: Optional callback for progress updates
        """
        self._extraction_progress = ExtractionProgress(start_time=datetime.now())

        project_path = Path(project_path)
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        # Ensure all collections exist
        await self.qdrant.ensure_all_unity_collections()

        # Load existing file hashes for incremental mode
        if incremental:
            await self._load_file_hashes()

        # Discover all relevant files
        files_to_process = await self._discover_files(project_path)
        self._extraction_progress.total_files = len(files_to_process)

        # Group files by type for parallel processing
        scripts = [f for f in files_to_process if f.suffix == ".cs"]
        scenes = [f for f in files_to_process if f.suffix == ".unity"]
        prefabs = [f for f in files_to_process if f.suffix == ".prefab"]
        assets = [f for f in files_to_process if f.suffix in {".mat", ".asset", ".controller"}]

        # Process in parallel by type
        tasks = [
            self._extract_scripts_batch(scripts, project_path, progress_callback),
            self._extract_scenes_batch(scenes, project_path, progress_callback),
            self._extract_prefabs_batch(prefabs, project_path, progress_callback),
            self._extract_assets_batch(assets, project_path, progress_callback),
        ]

        await asyncio.gather(*tasks)

        # Extract project settings
        await self._extract_project_settings(project_path)

        # Save file hashes for future incremental updates
        await self._save_file_hashes()

        self._extraction_progress.end_time = datetime.now()
        return self._extraction_progress

    async def _discover_files(self, project_path: Path) -> List[Path]:
        """Discover all Unity files to process."""
        files = []
        assets_path = project_path / "Assets"

        if not assets_path.exists():
            return files

        extensions = {".cs", ".unity", ".prefab", ".mat", ".asset", ".controller", ".anim"}
        exclude_dirs = {"Library", "Temp", "Logs", "obj", "Packages", ".git"}

        for root, dirs, filenames in os.walk(assets_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix in extensions:
                    # Check if file needs processing (incremental mode)
                    if self._should_process_file(file_path):
                        files.append(file_path)

        return files

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if file has changed since last extraction."""
        file_hash = self._compute_file_hash(file_path)
        stored_hash = self._file_hashes.get(str(file_path))

        if stored_hash != file_hash:
            self._file_hashes[str(file_path)] = file_hash
            return True
        return False

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    # ==================== C# SCRIPT EXTRACTION ====================

    async def _extract_scripts_batch(
        self,
        scripts: List[Path],
        project_path: Path,
        progress_callback: Optional[callable]
    ):
        """Extract all C# scripts in batches."""
        for i in range(0, len(scripts), self.batch_size):
            batch = scripts[i:i + self.batch_size]

            tasks = [
                self._extract_script(script, project_path)
                for script in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    self._extraction_progress.errors.append(str(result))
                else:
                    self._extraction_progress.scripts_extracted += 1
                    self._extraction_progress.processed_files += 1

            if progress_callback:
                progress_callback(self._extraction_progress)

    async def _extract_script(self, script_path: Path, project_path: Path) -> str:
        """Extract and index a single C# script."""
        try:
            content = script_path.read_text(encoding="utf-8-sig")
            relative_path = str(script_path.relative_to(project_path))

            classes = self._parse_csharp(content)

            if classes:
                return await self.qdrant.store_script(
                    file_path=relative_path,
                    content=content,
                    classes=[self._class_to_dict(c) for c in classes],
                    project_id=self.project_id,
                    metadata={
                        "line_count": content.count("\n") + 1,
                        "has_unity_callbacks": any(
                            m["name"] in self.UNITY_CALLBACKS
                            for c in classes
                            for m in c.methods
                        ),
                        "is_editor_script": "Editor" in relative_path,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to extract script {script_path}: {e}")
            raise

    def _parse_csharp(self, content: str) -> List[CSharpClass]:
        """Parse C# source code to extract class information."""
        classes = []

        # Extract namespace
        namespace_match = re.search(r"namespace\s+([\w.]+)", content)
        namespace = namespace_match.group(1) if namespace_match else None

        # Find all class/struct definitions
        class_pattern = r"""
            (?:(?P<attributes>\[[\w\s,()\"=]+\]\s*)*)
            (?P<modifiers>(?:public|private|protected|internal|abstract|sealed|static|partial)\s+)*
            (?P<type>class|struct|interface)\s+
            (?P<name>\w+)
            (?:\s*<[^>]+>)?  # Generic parameters
            (?:\s*:\s*(?P<bases>[^\{]+))?
            \s*\{
        """

        for match in re.finditer(class_pattern, content, re.VERBOSE | re.MULTILINE):
            class_name = match.group("name")
            modifiers = match.group("modifiers") or ""

            # Parse base classes and interfaces
            bases_str = match.group("bases") or ""
            bases = [b.strip() for b in bases_str.split(",") if b.strip()]
            base_classes = []
            interfaces = []

            for base in bases:
                # Remove generic parameters for base class detection
                base_clean = re.sub(r"<[^>]+>", "", base).strip()
                if base_clean.startswith("I") and base_clean[1].isupper():
                    interfaces.append(base_clean)
                else:
                    base_classes.append(base_clean)

            # Parse attributes
            attrs_str = match.group("attributes") or ""
            attributes = re.findall(r"\[(\w+)", attrs_str)

            # Extract class body
            class_start = match.end()
            class_body = self._extract_class_body(content, class_start)

            # Parse fields
            fields = self._parse_fields(class_body)

            # Parse properties
            properties = self._parse_properties(class_body)

            # Parse methods
            methods = self._parse_methods(class_body)

            classes.append(CSharpClass(
                name=class_name,
                namespace=namespace,
                base_classes=base_classes,
                interfaces=interfaces,
                attributes=attributes,
                fields=fields,
                properties=properties,
                methods=methods,
                is_abstract="abstract" in modifiers,
                is_partial="partial" in modifiers,
                is_static="static" in modifiers
            ))

        return classes

    def _extract_class_body(self, content: str, start: int) -> str:
        """Extract class body by matching braces."""
        brace_count = 1
        end = start

        for i, char in enumerate(content[start:], start):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    end = i
                    break

        return content[start:end]

    def _parse_fields(self, class_body: str) -> List[Dict[str, Any]]:
        """Parse class fields."""
        fields = []

        # Match field declarations
        field_pattern = r"""
            (?:(?P<attributes>\[[\w\s,()\"=]+\]\s*)*)
            (?P<modifiers>(?:public|private|protected|internal|static|readonly|const)\s+)*
            (?P<type>[\w<>\[\],\s\.]+?)\s+
            (?P<name>\w+)\s*
            (?:=\s*(?P<default>[^;]+))?\s*;
        """

        for match in re.finditer(field_pattern, class_body, re.VERBOSE | re.MULTILINE):
            # Skip method-looking things
            if "(" in match.group(0):
                continue

            modifiers = match.group("modifiers") or ""
            attrs_str = match.group("attributes") or ""
            attributes = re.findall(r"\[(\w+)", attrs_str)

            fields.append({
                "name": match.group("name"),
                "type": match.group("type").strip(),
                "is_public": "public" in modifiers,
                "is_serialized": "SerializeField" in attributes or "public" in modifiers,
                "is_static": "static" in modifiers,
                "is_readonly": "readonly" in modifiers,
                "attributes": attributes,
                "default_value": match.group("default"),
            })

        return fields

    def _parse_properties(self, class_body: str) -> List[Dict[str, Any]]:
        """Parse class properties."""
        properties = []

        prop_pattern = r"""
            (?P<modifiers>(?:public|private|protected|internal|static|virtual|override|abstract)\s+)+
            (?P<type>[\w<>\[\],\s\.]+?)\s+
            (?P<name>\w+)\s*
            \{\s*(?P<accessors>[^}]+)\}
        """

        for match in re.finditer(prop_pattern, class_body, re.VERBOSE | re.MULTILINE):
            modifiers = match.group("modifiers") or ""
            accessors = match.group("accessors") or ""

            properties.append({
                "name": match.group("name"),
                "type": match.group("type").strip(),
                "is_public": "public" in modifiers,
                "has_getter": "get" in accessors,
                "has_setter": "set" in accessors,
                "is_virtual": "virtual" in modifiers,
            })

        return properties

    def _parse_methods(self, class_body: str) -> List[Dict[str, Any]]:
        """Parse class methods."""
        methods = []

        method_pattern = r"""
            (?:(?P<attributes>\[[\w\s,()\"=]+\]\s*)*)
            (?P<modifiers>(?:public|private|protected|internal|static|virtual|override|abstract|async)\s+)*
            (?P<return_type>[\w<>\[\],\s\.]+?)\s+
            (?P<name>\w+)\s*
            (?:<[^>]+>)?\s*  # Generic parameters
            \((?P<params>[^)]*)\)\s*
            (?:where[^{]+)?  # Generic constraints
            (?:\{|;|=>)
        """

        for match in re.finditer(method_pattern, class_body, re.VERBOSE | re.MULTILINE):
            name = match.group("name")
            modifiers = match.group("modifiers") or ""

            # Parse parameters
            params_str = match.group("params") or ""
            params = self._parse_parameters(params_str)

            attrs_str = match.group("attributes") or ""
            attributes = re.findall(r"\[(\w+)", attrs_str)

            methods.append({
                "name": name,
                "return_type": match.group("return_type").strip(),
                "parameters": params,
                "is_public": "public" in modifiers,
                "is_static": "static" in modifiers,
                "is_virtual": "virtual" in modifiers,
                "is_override": "override" in modifiers,
                "is_async": "async" in modifiers,
                "is_unity_callback": name in self.UNITY_CALLBACKS,
                "attributes": attributes,
            })

        return methods

    def _parse_parameters(self, params_str: str) -> List[Tuple[str, str]]:
        """Parse method parameters."""
        if not params_str.strip():
            return []

        params = []
        for param in params_str.split(","):
            param = param.strip()
            if not param:
                continue

            # Remove modifiers like 'ref', 'out', 'in', 'params'
            param = re.sub(r"^(ref|out|in|params)\s+", "", param)

            # Remove default values
            param = re.sub(r"\s*=.*$", "", param)

            parts = param.rsplit(" ", 1)
            if len(parts) == 2:
                params.append((parts[1], parts[0]))

        return params

    def _class_to_dict(self, cls: CSharpClass) -> Dict[str, Any]:
        """Convert CSharpClass to dictionary."""
        return {
            "name": cls.name,
            "namespace": cls.namespace,
            "base_classes": cls.base_classes,
            "interfaces": cls.interfaces,
            "attributes": cls.attributes,
            "fields": cls.fields,
            "properties": cls.properties,
            "methods": cls.methods,
            "is_abstract": cls.is_abstract,
            "is_partial": cls.is_partial,
            "is_static": cls.is_static,
        }

    # ==================== SCENE EXTRACTION ====================

    async def _extract_scenes_batch(
        self,
        scenes: List[Path],
        project_path: Path,
        progress_callback: Optional[callable]
    ):
        """Extract all scenes in batches."""
        for scene_path in scenes:
            try:
                await self._extract_scene(scene_path, project_path)
                self._extraction_progress.scenes_extracted += 1
                self._extraction_progress.processed_files += 1

            except Exception as e:
                self._extraction_progress.errors.append(f"Scene {scene_path}: {e}")

            if progress_callback:
                progress_callback(self._extraction_progress)

    async def _extract_scene(self, scene_path: Path, project_path: Path) -> str:
        """Extract and index a Unity scene."""
        try:
            content = scene_path.read_text(encoding="utf-8-sig")
            relative_path = str(scene_path.relative_to(project_path))
            scene_name = scene_path.stem

            game_objects = self._parse_unity_yaml(content)

            # Create scene content summary
            scene_content = self._create_scene_summary(scene_name, game_objects)

            return await self.qdrant.store_scene(
                scene_name=scene_name,
                scene_path=relative_path,
                content=scene_content,
                game_objects=[self._gameobject_to_dict(go) for go in game_objects],
                project_id=self.project_id,
                metadata={
                    "gameobject_count": len(game_objects),
                    "root_count": len([go for go in game_objects if not go.parent_id]),
                }
            )

        except Exception as e:
            logger.error(f"Failed to extract scene {scene_path}: {e}")
            raise

    def _parse_unity_yaml(self, content: str) -> List[UnityGameObject]:
        """Parse Unity YAML scene/prefab file."""
        game_objects = []

        # Unity YAML uses --- separators for documents
        # Each document starts with a type identifier

        # Simple regex-based parsing for GameObjects
        go_pattern = r"--- !u!1 &(\d+)\s*GameObject:\s*m_ObjectHideFlags: \d+[\s\S]*?m_Name: ([^\n]+)[\s\S]*?m_TagString: ([^\n]+)[\s\S]*?m_Layer: (\d+)"

        for match in re.finditer(go_pattern, content):
            file_id = match.group(1)
            name = match.group(2).strip()
            tag = match.group(3).strip()
            layer = int(match.group(4))

            # Extract components for this GameObject
            components = self._extract_components(content, file_id)

            # Find parent from Transform component
            parent_id = None
            transform = None
            for comp in components:
                if comp.get("type") in ["Transform", "RectTransform"]:
                    transform = comp
                    parent_ref = comp.get("parent")
                    if parent_ref:
                        parent_id = parent_ref

            game_objects.append(UnityGameObject(
                name=name,
                file_id=file_id,
                tag=tag,
                layer=layer,
                is_active=True,
                components=components,
                children_ids=[],
                parent_id=parent_id,
                transform=transform
            ))

        # Build parent-child relationships
        go_by_id = {go.file_id: go for go in game_objects}
        for go in game_objects:
            if go.parent_id and go.parent_id in go_by_id:
                go_by_id[go.parent_id].children_ids.append(go.file_id)

        return game_objects

    def _extract_components(self, content: str, gameobject_id: str) -> List[Dict[str, Any]]:
        """Extract components attached to a GameObject."""
        components = []

        # Find component references in the GameObject
        go_section = re.search(
            rf"--- !u!1 &{gameobject_id}[\s\S]*?(?=--- !u!|$)",
            content
        )

        if not go_section:
            return components

        # Find component file IDs
        comp_refs = re.findall(r"component:\s*\{fileID: (\d+)\}", go_section.group())

        # Common Unity component type IDs
        component_types = {
            "4": "Transform",
            "20": "Camera",
            "23": "MeshRenderer",
            "33": "MeshFilter",
            "54": "Rigidbody",
            "65": "BoxCollider",
            "82": "AudioSource",
            "108": "Light",
            "114": "MonoBehaviour",
            "135": "SphereCollider",
            "136": "CapsuleCollider",
            "137": "SkinnedMeshRenderer",
            "224": "RectTransform",
            "225": "CanvasRenderer",
            "226": "Canvas",
        }

        for comp_id in comp_refs:
            # Find component section
            comp_match = re.search(
                rf"--- !u!(\d+) &{comp_id}[\s\S]*?(?=--- !u!|$)",
                content
            )

            if comp_match:
                type_id = comp_match.group(1)
                comp_type = component_types.get(type_id, f"Component_{type_id}")

                comp_data = {"type": comp_type, "file_id": comp_id}

                # For MonoBehaviour, try to get script reference
                if type_id == "114":
                    script_match = re.search(
                        r"m_Script:\s*\{fileID: \d+, guid: ([a-f0-9]+)",
                        comp_match.group()
                    )
                    if script_match:
                        comp_data["script_guid"] = script_match.group(1)

                # For Transform, get parent reference
                if type_id in ["4", "224"]:
                    parent_match = re.search(
                        r"m_Father:\s*\{fileID: (\d+)\}",
                        comp_match.group()
                    )
                    if parent_match and parent_match.group(1) != "0":
                        comp_data["parent"] = parent_match.group(1)

                components.append(comp_data)

        return components

    def _gameobject_to_dict(self, go: UnityGameObject) -> Dict[str, Any]:
        """Convert UnityGameObject to dictionary."""
        return {
            "name": go.name,
            "file_id": go.file_id,
            "tag": go.tag,
            "layer": go.layer,
            "is_active": go.is_active,
            "components": go.components,
            "children": go.children_ids,
            "parent": go.parent_id,
        }

    def _create_scene_summary(
        self,
        scene_name: str,
        game_objects: List[UnityGameObject]
    ) -> str:
        """Create searchable summary of scene."""
        parts = [f"Unity Scene: {scene_name}"]
        parts.append(f"Total GameObjects: {len(game_objects)}")

        # Root objects
        roots = [go for go in game_objects if not go.parent_id]
        parts.append(f"Root Objects: {', '.join(go.name for go in roots[:20])}")

        # Component summary
        comp_counts: Dict[str, int] = {}
        for go in game_objects:
            for comp in go.components:
                comp_type = comp.get("type", "Unknown")
                comp_counts[comp_type] = comp_counts.get(comp_type, 0) + 1

        parts.append("Components:")
        for comp, count in sorted(comp_counts.items(), key=lambda x: -x[1])[:15]:
            parts.append(f"  - {comp}: {count}")

        # Tags used
        tags = set(go.tag for go in game_objects if go.tag != "Untagged")
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")

        return "\n".join(parts)

    # ==================== PREFAB EXTRACTION ====================

    async def _extract_prefabs_batch(
        self,
        prefabs: List[Path],
        project_path: Path,
        progress_callback: Optional[callable]
    ):
        """Extract all prefabs in batches."""
        for i in range(0, len(prefabs), self.batch_size):
            batch = prefabs[i:i + self.batch_size]

            tasks = [
                self._extract_prefab(prefab, project_path)
                for prefab in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    self._extraction_progress.errors.append(str(result))
                else:
                    self._extraction_progress.prefabs_extracted += 1
                    self._extraction_progress.processed_files += 1

            if progress_callback:
                progress_callback(self._extraction_progress)

    async def _extract_prefab(self, prefab_path: Path, project_path: Path) -> str:
        """Extract and index a Unity prefab."""
        try:
            content = prefab_path.read_text(encoding="utf-8-sig")
            relative_path = str(prefab_path.relative_to(project_path))
            prefab_name = prefab_path.stem

            game_objects = self._parse_unity_yaml(content)

            # Get GUID from meta file
            meta_path = prefab_path.with_suffix(prefab_path.suffix + ".meta")
            guid = ""
            if meta_path.exists():
                meta_content = meta_path.read_text()
                guid_match = re.search(r"guid:\s*([a-f0-9]+)", meta_content)
                if guid_match:
                    guid = guid_match.group(1)

            # Create prefab content
            prefab_content = f"Unity Prefab: {prefab_name}\n"
            prefab_content += f"Path: {relative_path}\n"
            prefab_content += f"GameObjects: {len(game_objects)}\n"

            root_go = next((go for go in game_objects if not go.parent_id), None)
            if root_go:
                prefab_content += f"Root Components: {', '.join(c.get('type', '') for c in root_go.components)}"

            return await self.qdrant.store_asset(
                asset_path=relative_path,
                asset_type="Prefab",
                guid=guid,
                project_id=self.project_id,
                metadata={
                    "prefab_name": prefab_name,
                    "gameobject_count": len(game_objects),
                    "components": list(set(
                        c.get("type", "") for go in game_objects for c in go.components
                    )),
                    "entity_type": "prefab",
                }
            )

        except Exception as e:
            logger.error(f"Failed to extract prefab {prefab_path}: {e}")
            raise

    # ==================== ASSET EXTRACTION ====================

    async def _extract_assets_batch(
        self,
        assets: List[Path],
        project_path: Path,
        progress_callback: Optional[callable]
    ):
        """Extract all assets in batches."""
        for i in range(0, len(assets), self.batch_size):
            batch = assets[i:i + self.batch_size]

            tasks = [
                self._extract_asset(asset, project_path)
                for asset in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    self._extraction_progress.errors.append(str(result))
                else:
                    self._extraction_progress.assets_extracted += 1
                    self._extraction_progress.processed_files += 1

            if progress_callback:
                progress_callback(self._extraction_progress)

    async def _extract_asset(self, asset_path: Path, project_path: Path) -> str:
        """Extract and index a Unity asset."""
        try:
            relative_path = str(asset_path.relative_to(project_path))

            # Determine asset type
            asset_type_map = {
                ".mat": "Material",
                ".asset": "ScriptableObject",
                ".controller": "AnimatorController",
                ".anim": "AnimationClip",
                ".shader": "Shader",
            }
            asset_type = asset_type_map.get(asset_path.suffix, "Asset")

            # Get GUID from meta file
            meta_path = asset_path.with_suffix(asset_path.suffix + ".meta")
            guid = ""
            dependencies = []

            if meta_path.exists():
                meta_content = meta_path.read_text()
                guid_match = re.search(r"guid:\s*([a-f0-9]+)", meta_content)
                if guid_match:
                    guid = guid_match.group(1)

            # Parse asset content for dependencies
            try:
                content = asset_path.read_text(encoding="utf-8-sig")
                dep_guids = re.findall(r"guid:\s*([a-f0-9]{32})", content)
                dependencies = list(set(dep_guids) - {guid})
            except Exception:
                pass

            return await self.qdrant.store_asset(
                asset_path=relative_path,
                asset_type=asset_type,
                guid=guid,
                project_id=self.project_id,
                dependencies=dependencies[:20],  # Limit dependencies
                metadata={
                    "file_size": asset_path.stat().st_size,
                }
            )

        except Exception as e:
            logger.error(f"Failed to extract asset {asset_path}: {e}")
            raise

    # ==================== PROJECT SETTINGS ====================

    async def _extract_project_settings(self, project_path: Path):
        """Extract Unity project settings."""
        settings_path = project_path / "ProjectSettings"
        if not settings_path.exists():
            return

        # Key settings files to extract
        settings_files = [
            "ProjectSettings.asset",
            "TagManager.asset",
            "InputManager.asset",
            "QualitySettings.asset",
        ]

        for settings_file in settings_files:
            file_path = settings_path / settings_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8-sig")

                    # Extract Unity version
                    version_match = re.search(r"m_EditorVersion:\s*(.+)", content)
                    unity_version = version_match.group(1).strip() if version_match else "Unknown"

                    await self.qdrant.store_asset(
                        asset_path=f"ProjectSettings/{settings_file}",
                        asset_type="ProjectSettings",
                        guid=settings_file,
                        project_id=self.project_id,
                        metadata={
                            "unity_version": unity_version,
                            "settings_type": settings_file.replace(".asset", ""),
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to extract settings {file_path}: {e}")

    # ==================== FILE HASH PERSISTENCE ====================

    async def _load_file_hashes(self):
        """Load stored file hashes for incremental updates."""
        # In a real implementation, this would load from Qdrant or local file
        # For now, start fresh each time
        self._file_hashes = {}

    async def _save_file_hashes(self):
        """Save file hashes for future incremental updates."""
        # Store in project state collection
        try:
            content = json.dumps(self._file_hashes)
            await self.qdrant.store_asset(
                asset_path="__internal__/file_hashes.json",
                asset_type="InternalState",
                guid="file_hashes",
                project_id=self.project_id,
                metadata={
                    "hash_count": len(self._file_hashes),
                    "last_updated": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to save file hashes: {e}")


class UnityKnowledgeWatcher:
    """
    Watch Unity project for changes and update knowledge base in real-time.
    """

    def __init__(
        self,
        extractor: UnityKnowledgeExtractor,
        project_path: str,
        debounce_seconds: float = 2.0
    ):
        self.extractor = extractor
        self.project_path = Path(project_path)
        self.debounce_seconds = debounce_seconds
        self._pending_updates: Set[Path] = set()
        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start watching for file changes."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.warning("watchdog not installed, file watching disabled")
            return

        self._running = True

        class UnityFileHandler(FileSystemEventHandler):
            def __init__(handler_self, watcher):
                handler_self.watcher = watcher

            def on_modified(handler_self, event):
                if not event.is_directory:
                    path = Path(event.src_path)
                    if path.suffix in {".cs", ".unity", ".prefab", ".mat", ".asset"}:
                        asyncio.create_task(
                            handler_self.watcher._queue_update(path)
                        )

        handler = UnityFileHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.project_path / "Assets"), recursive=True)
        observer.start()

        logger.info(f"Watching Unity project: {self.project_path}")

    async def _queue_update(self, path: Path):
        """Queue a file for update with debouncing."""
        self._pending_updates.add(path)

        if self._update_task:
            self._update_task.cancel()

        self._update_task = asyncio.create_task(self._process_updates())

    async def _process_updates(self):
        """Process pending updates after debounce period."""
        await asyncio.sleep(self.debounce_seconds)

        updates = list(self._pending_updates)
        self._pending_updates.clear()

        for path in updates:
            try:
                if path.suffix == ".cs":
                    await self.extractor._extract_script(path, self.project_path)
                elif path.suffix == ".unity":
                    await self.extractor._extract_scene(path, self.project_path)
                elif path.suffix == ".prefab":
                    await self.extractor._extract_prefab(path, self.project_path)
                else:
                    await self.extractor._extract_asset(path, self.project_path)

                logger.info(f"Updated knowledge for: {path}")

            except Exception as e:
                logger.error(f"Failed to update {path}: {e}")

    def stop(self):
        """Stop watching."""
        self._running = False
