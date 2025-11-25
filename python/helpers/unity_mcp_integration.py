"""
Unity MCP Integration Layer.

Provides communication with Unity Editor through MCP (Model Context Protocol)
for real-time project manipulation and state synchronization.

Features:
- Scene manipulation (load, save, create objects)
- Asset management (create, import, modify)
- Build pipeline control
- Play mode control
- Console log streaming
- Hot reload triggering
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import aiohttp
from pathlib import Path

from python.helpers.unity_qdrant_enhanced import UnityQdrantEnhanced
from python.helpers.unity_project_tracker import UnityProjectTracker

logger = logging.getLogger(__name__)


class UnityCommand(Enum):
    """Available Unity Editor commands via MCP."""
    # Scene commands
    LOAD_SCENE = "LoadScene"
    SAVE_SCENE = "SaveScene"
    CREATE_SCENE = "CreateScene"
    GET_SCENE_INFO = "GetSceneInfo"
    GET_HIERARCHY = "GetHierarchy"

    # GameObject commands
    CREATE_GAMEOBJECT = "CreateGameObject"
    DELETE_GAMEOBJECT = "DeleteGameObject"
    MODIFY_GAMEOBJECT = "ModifyGameObject"
    ADD_COMPONENT = "AddComponent"
    REMOVE_COMPONENT = "RemoveComponent"
    GET_COMPONENT = "GetComponent"
    SET_COMPONENT_PROPERTY = "SetComponentProperty"

    # Asset commands
    CREATE_PREFAB = "CreatePrefab"
    IMPORT_ASSET = "ImportAsset"
    DELETE_ASSET = "DeleteAsset"
    REFRESH_ASSETS = "RefreshAssets"
    GET_ASSET_INFO = "GetAssetInfo"
    CREATE_MATERIAL = "CreateMaterial"
    CREATE_SCRIPTABLE_OBJECT = "CreateScriptableObject"

    # Script commands
    CREATE_SCRIPT = "CreateScript"
    COMPILE_SCRIPTS = "CompileScripts"
    GET_SCRIPT_ERRORS = "GetScriptErrors"
    HOT_RELOAD = "HotReload"

    # Build commands
    BUILD_PLAYER = "BuildPlayer"
    BUILD_ASSET_BUNDLES = "BuildAssetBundles"
    GET_BUILD_SETTINGS = "GetBuildSettings"
    SET_BUILD_TARGET = "SetBuildTarget"

    # Play mode
    ENTER_PLAY_MODE = "EnterPlayMode"
    EXIT_PLAY_MODE = "ExitPlayMode"
    PAUSE_PLAY_MODE = "PausePlayMode"
    GET_PLAY_MODE_STATE = "GetPlayModeState"

    # Console
    GET_CONSOLE_LOGS = "GetConsoleLogs"
    CLEAR_CONSOLE = "ClearConsole"
    SUBSCRIBE_LOGS = "SubscribeLogs"

    # Project
    GET_PROJECT_INFO = "GetProjectInfo"
    GET_PROJECT_SETTINGS = "GetProjectSettings"
    SET_PROJECT_SETTING = "SetProjectSetting"

    # Selection
    GET_SELECTION = "GetSelection"
    SET_SELECTION = "SetSelection"
    FOCUS_OBJECT = "FocusObject"


@dataclass
class MCPCommand:
    """MCP command structure."""
    command: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    callback_id: Optional[str] = None


@dataclass
class MCPResponse:
    """MCP response structure."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class UnityLogEntry:
    """Unity console log entry."""
    message: str
    stack_trace: str
    log_type: str  # Log, Warning, Error, Exception
    timestamp: datetime
    context: Optional[str] = None


@dataclass
class UnityEditorState:
    """Current state of Unity Editor."""
    is_playing: bool = False
    is_paused: bool = False
    is_compiling: bool = False
    active_scene: str = ""
    selected_objects: List[str] = field(default_factory=list)
    last_error: Optional[str] = None
    unity_version: str = ""


class UnityMCPClient:
    """
    Client for communicating with Unity Editor via MCP server.

    Features:
    - Async HTTP communication
    - Automatic reconnection
    - Command batching
    - Event streaming (logs, state changes)
    - Error recovery
    """

    def __init__(
        self,
        mcp_url: str = "http://localhost:9050",
        timeout: float = 30.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):
        self.mcp_url = mcp_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._state = UnityEditorState()
        self._log_callbacks: List[Callable[[UnityLogEntry], None]] = []
        self._state_callbacks: List[Callable[[UnityEditorState], None]] = []

    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        try:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

            # Test connection
            async with self._session.get(f"{self.mcp_url}/health") as response:
                if response.status == 200:
                    self._connected = True
                    logger.info(f"Connected to Unity MCP at {self.mcp_url}")

                    # Get initial state
                    await self._update_state()
                    return True

        except Exception as e:
            logger.error(f"Failed to connect to Unity MCP: {e}")
            self._connected = False

        return False

    async def disconnect(self):
        """Close connection."""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False

    async def is_connected(self) -> bool:
        """Check if connected to Unity."""
        if not self._connected or not self._session:
            return False

        try:
            async with self._session.get(
                f"{self.mcp_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def execute(
        self,
        command: UnityCommand,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> MCPResponse:
        """Execute a Unity command."""
        if not self._connected:
            await self.connect()

        if not self._connected:
            return MCPResponse(
                success=False,
                error="Not connected to Unity MCP server"
            )

        cmd = MCPCommand(
            command=command.value,
            parameters=parameters or {},
            timeout=timeout or self.timeout,
        )

        return await self._send_command(cmd)

    async def _send_command(self, cmd: MCPCommand) -> MCPResponse:
        """Send command to MCP server with retry."""
        start_time = time.time()

        for attempt in range(self.retry_attempts):
            try:
                async with self._session.post(
                    f"{self.mcp_url}/api/command",
                    json={
                        "command": cmd.command,
                        "parameters": cmd.parameters,
                    },
                    timeout=aiohttp.ClientTimeout(total=cmd.timeout)
                ) as response:
                    data = await response.json()

                    duration_ms = (time.time() - start_time) * 1000

                    if response.status == 200 and data.get("success"):
                        return MCPResponse(
                            success=True,
                            data=data.get("result"),
                            duration_ms=duration_ms,
                        )
                    else:
                        return MCPResponse(
                            success=False,
                            error=data.get("error", "Unknown error"),
                            duration_ms=duration_ms,
                        )

            except asyncio.TimeoutError:
                logger.warning(f"Command timeout: {cmd.command} (attempt {attempt + 1})")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)

            except Exception as e:
                logger.error(f"Command error: {cmd.command} - {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)

        return MCPResponse(
            success=False,
            error=f"Command failed after {self.retry_attempts} attempts",
            duration_ms=(time.time() - start_time) * 1000,
        )

    async def _update_state(self):
        """Update editor state from Unity."""
        try:
            response = await self.execute(UnityCommand.GET_PROJECT_INFO)
            if response.success and response.data:
                self._state.unity_version = response.data.get("unityVersion", "")
                self._state.active_scene = response.data.get("activeScene", "")

            response = await self.execute(UnityCommand.GET_PLAY_MODE_STATE)
            if response.success and response.data:
                self._state.is_playing = response.data.get("isPlaying", False)
                self._state.is_paused = response.data.get("isPaused", False)

            response = await self.execute(UnityCommand.GET_SELECTION)
            if response.success and response.data:
                self._state.selected_objects = response.data.get("selection", [])

        except Exception as e:
            logger.error(f"Failed to update state: {e}")

    @property
    def state(self) -> UnityEditorState:
        """Get current editor state."""
        return self._state

    def on_log(self, callback: Callable[[UnityLogEntry], None]):
        """Register callback for log events."""
        self._log_callbacks.append(callback)

    def on_state_change(self, callback: Callable[[UnityEditorState], None]):
        """Register callback for state changes."""
        self._state_callbacks.append(callback)

    # ==================== HIGH-LEVEL API ====================

    async def load_scene(self, scene_path: str) -> MCPResponse:
        """Load a scene in the Editor."""
        return await self.execute(
            UnityCommand.LOAD_SCENE,
            {"scenePath": scene_path}
        )

    async def save_scene(self, scene_path: Optional[str] = None) -> MCPResponse:
        """Save the current scene."""
        params = {}
        if scene_path:
            params["scenePath"] = scene_path
        return await self.execute(UnityCommand.SAVE_SCENE, params)

    async def create_gameobject(
        self,
        name: str,
        parent: Optional[str] = None,
        position: Optional[List[float]] = None,
        rotation: Optional[List[float]] = None,
    ) -> MCPResponse:
        """Create a new GameObject."""
        params = {"name": name}
        if parent:
            params["parent"] = parent
        if position:
            params["position"] = position
        if rotation:
            params["rotation"] = rotation

        return await self.execute(UnityCommand.CREATE_GAMEOBJECT, params)

    async def add_component(
        self,
        gameobject: str,
        component_type: str,
    ) -> MCPResponse:
        """Add a component to a GameObject."""
        return await self.execute(
            UnityCommand.ADD_COMPONENT,
            {
                "gameObject": gameobject,
                "componentType": component_type,
            }
        )

    async def set_component_property(
        self,
        gameobject: str,
        component_type: str,
        property_name: str,
        value: Any,
    ) -> MCPResponse:
        """Set a component property value."""
        return await self.execute(
            UnityCommand.SET_COMPONENT_PROPERTY,
            {
                "gameObject": gameobject,
                "componentType": component_type,
                "propertyName": property_name,
                "value": value,
            }
        )

    async def create_prefab(
        self,
        source_gameobject: str,
        prefab_path: str,
    ) -> MCPResponse:
        """Create a prefab from a GameObject."""
        return await self.execute(
            UnityCommand.CREATE_PREFAB,
            {
                "sourceGameObject": source_gameobject,
                "prefabPath": prefab_path,
            }
        )

    async def create_script(
        self,
        script_name: str,
        script_path: str,
        template: str = "MonoBehaviour",
        namespace: Optional[str] = None,
    ) -> MCPResponse:
        """Create a new C# script."""
        params = {
            "scriptName": script_name,
            "scriptPath": script_path,
            "template": template,
        }
        if namespace:
            params["namespace"] = namespace

        return await self.execute(UnityCommand.CREATE_SCRIPT, params)

    async def hot_reload(self) -> MCPResponse:
        """Trigger script hot reload."""
        return await self.execute(UnityCommand.HOT_RELOAD)

    async def get_script_errors(self) -> MCPResponse:
        """Get current script compilation errors."""
        return await self.execute(UnityCommand.GET_SCRIPT_ERRORS)

    async def build_player(
        self,
        target: str,
        output_path: str,
        scenes: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> MCPResponse:
        """Build the player."""
        params = {
            "target": target,
            "outputPath": output_path,
        }
        if scenes:
            params["scenes"] = scenes
        if options:
            params["options"] = options

        return await self.execute(
            UnityCommand.BUILD_PLAYER,
            params,
            timeout=300  # 5 minute timeout for builds
        )

    async def enter_play_mode(self) -> MCPResponse:
        """Enter play mode."""
        return await self.execute(UnityCommand.ENTER_PLAY_MODE)

    async def exit_play_mode(self) -> MCPResponse:
        """Exit play mode."""
        return await self.execute(UnityCommand.EXIT_PLAY_MODE)

    async def get_console_logs(
        self,
        log_types: Optional[List[str]] = None,
        limit: int = 100,
    ) -> MCPResponse:
        """Get console logs."""
        params = {"limit": limit}
        if log_types:
            params["logTypes"] = log_types

        return await self.execute(UnityCommand.GET_CONSOLE_LOGS, params)

    async def get_hierarchy(
        self,
        scene: Optional[str] = None,
        depth: int = 10,
    ) -> MCPResponse:
        """Get scene hierarchy."""
        params = {"depth": depth}
        if scene:
            params["scene"] = scene

        return await self.execute(UnityCommand.GET_HIERARCHY, params)

    async def focus_object(self, gameobject: str) -> MCPResponse:
        """Focus on a GameObject in the Scene view."""
        return await self.execute(
            UnityCommand.FOCUS_OBJECT,
            {"gameObject": gameobject}
        )


class UnityMCPIntegration:
    """
    High-level integration between Agent Zero and Unity Editor.

    Coordinates:
    - MCP communication
    - Knowledge base updates
    - Project state tracking
    - Error synchronization
    """

    def __init__(
        self,
        mcp_client: UnityMCPClient,
        qdrant: UnityQdrantEnhanced,
        project_id: str,
        project_tracker: Optional[UnityProjectTracker] = None,
    ):
        self.mcp = mcp_client
        self.qdrant = qdrant
        self.project_id = project_id
        self.tracker = project_tracker

        # Register callbacks
        self.mcp.on_log(self._handle_log)
        self.mcp.on_state_change(self._handle_state_change)

    async def initialize(self) -> bool:
        """Initialize the integration."""
        connected = await self.mcp.connect()
        if connected:
            # Sync initial state
            await self._sync_project_info()
            logger.info("Unity MCP integration initialized")
        return connected

    async def _sync_project_info(self):
        """Sync project information from Unity."""
        response = await self.mcp.execute(UnityCommand.GET_PROJECT_INFO)
        if response.success and response.data:
            # Store project info
            await self.qdrant.store_asset(
                asset_path="__internal__/project_info.json",
                asset_type="InternalState",
                guid="project_info",
                project_id=self.project_id,
                metadata={
                    "unity_version": response.data.get("unityVersion"),
                    "project_name": response.data.get("projectName"),
                    "active_scene": response.data.get("activeScene"),
                    "synced_at": datetime.now().isoformat(),
                }
            )

    def _handle_log(self, log: UnityLogEntry):
        """Handle Unity console log."""
        if log.log_type in ["Error", "Exception"]:
            # Store error in knowledge base
            asyncio.create_task(
                self._store_error(log)
            )

            # Notify tracker
            if self.tracker:
                asyncio.create_task(
                    self.tracker.record_error(
                        error_type=log.log_type,
                        error_message=log.message,
                        stack_trace=log.stack_trace,
                    )
                )

    async def _store_error(self, log: UnityLogEntry):
        """Store error in knowledge base."""
        await self.qdrant.store_error(
            error_message=log.message,
            error_type=log.log_type,
            stack_trace=log.stack_trace,
            project_id=self.project_id,
            metadata={
                "context": log.context,
                "timestamp": log.timestamp.isoformat(),
            }
        )

    def _handle_state_change(self, state: UnityEditorState):
        """Handle Unity state change."""
        logger.debug(f"Unity state changed: playing={state.is_playing}")

        # Could trigger knowledge sync on scene change
        if state.active_scene:
            asyncio.create_task(
                self._sync_scene(state.active_scene)
            )

    async def _sync_scene(self, scene_name: str):
        """Sync scene data from Unity."""
        response = await self.mcp.get_hierarchy()
        if response.success and response.data:
            # Scene data would be processed and stored
            logger.debug(f"Synced scene: {scene_name}")

    # ==================== HIGH-LEVEL OPERATIONS ====================

    async def create_and_track_gameobject(
        self,
        name: str,
        components: Optional[List[str]] = None,
        parent: Optional[str] = None,
        store_in_memory: bool = True,
    ) -> MCPResponse:
        """Create a GameObject and optionally track it in memory."""
        response = await self.mcp.create_gameobject(name, parent)

        if response.success:
            # Add components
            if components:
                for comp in components:
                    await self.mcp.add_component(name, comp)

            # Store in knowledge base
            if store_in_memory:
                scene = self.mcp.state.active_scene
                await self.qdrant.aadd_documents(
                    documents=[{
                        "page_content": f"GameObject: {name}\nComponents: {', '.join(components or [])}",
                        "metadata": {
                            "entity_type": "gameobject",
                            "entity_name": name,
                            "scene_name": scene,
                            "components": components or [],
                            "parent": parent,
                            "created_by": "agent",
                            "timestamp": datetime.now().isoformat(),
                        }
                    }],
                    ids=[f"go:{self.project_id}:{scene}:{name}"]
                )

        return response

    async def create_and_track_script(
        self,
        script_name: str,
        script_path: str,
        content: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> MCPResponse:
        """Create a script and track it in memory."""
        response = await self.mcp.create_script(
            script_name, script_path, namespace=namespace
        )

        if response.success:
            # If content provided, write it
            if content:
                full_path = os.path.join(
                    str(self.project_id), "Assets", script_path
                )
                # Would need file system access here

            # Store in knowledge base
            await self.qdrant.store_script(
                file_path=f"Assets/{script_path}",
                content=content or f"// {script_name}.cs",
                classes=[{
                    "name": script_name,
                    "namespace": namespace,
                    "base_classes": ["MonoBehaviour"],
                    "methods": [],
                    "fields": [],
                }],
                project_id=self.project_id,
                metadata={
                    "created_by": "agent",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return response

    async def build_with_tracking(
        self,
        target: str,
        output_path: str,
        scenes: Optional[List[str]] = None,
    ) -> MCPResponse:
        """Build player with tracking."""
        if self.tracker:
            build_id = await self.tracker.start_build(target)

        response = await self.mcp.build_player(target, output_path, scenes)

        if self.tracker:
            errors = []
            if response.data and response.data.get("errors"):
                errors = response.data["errors"]

            await self.tracker.finish_build(
                success=response.success,
                errors=errors,
                output_path=output_path if response.success else None,
            )

        return response

    async def get_context_for_scene(self, scene_name: str) -> Dict[str, Any]:
        """Get comprehensive context for a scene."""
        context = {
            "scene": scene_name,
            "hierarchy": None,
            "scripts": [],
            "errors": [],
            "recent_changes": [],
        }

        # Get hierarchy from Unity
        hierarchy_response = await self.mcp.get_hierarchy()
        if hierarchy_response.success:
            context["hierarchy"] = hierarchy_response.data

        # Get related scripts from memory
        script_results = await self.qdrant.search_unity(
            query=f"scripts used in {scene_name}",
            collection_types=[UnityCollectionType.SCRIPTS],
            project_id=self.project_id,
            limit=20,
        )
        context["scripts"] = [
            r.document.metadata for r in script_results
        ]

        # Get recent errors
        error_results = await self.qdrant.search_unity(
            query=scene_name,
            collection_types=[UnityCollectionType.ERRORS],
            project_id=self.project_id,
            limit=10,
        )
        context["errors"] = [
            {
                "message": r.document.metadata.get("error_message"),
                "type": r.document.metadata.get("error_type"),
            }
            for r in error_results
        ]

        return context

    async def suggest_fixes_for_errors(self) -> List[Dict[str, Any]]:
        """Get current errors and suggest fixes from memory."""
        suggestions = []

        # Get errors from Unity
        error_response = await self.mcp.get_script_errors()
        if error_response.success and error_response.data:
            errors = error_response.data.get("errors", [])

            for error in errors:
                message = error.get("message", "")

                # Search for solutions in memory
                solutions = await self.qdrant.find_similar_errors(
                    message, project_id=self.project_id
                )

                suggestions.append({
                    "error": error,
                    "solutions": [
                        {
                            "description": s.document.metadata.get("solution"),
                            "score": s.score,
                        }
                        for s in solutions if s.document.metadata.get("has_solution")
                    ],
                })

        return suggestions
