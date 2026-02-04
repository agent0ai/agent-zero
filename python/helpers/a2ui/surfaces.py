"""A2UI Surface Manager - Lifecycle management for rendering surfaces.

Manages the state and lifecycle of A2UI surfaces, tracking active surfaces,
their components, and data models for incremental updates.

Per A2UI v0.8 specification:
- Surfaces are identified by unique surfaceId
- Components are stored in an adjacency list (flat list with ID references)
- Data model provides reactive bindings for dynamic content
"""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .types import (
    A2UIComponent,
    BeginRenderingContent,
    BeginRenderingMessage,
    SurfaceUpdateContent,
    SurfaceUpdateMessage,
    DeleteSurfaceContent,
    DeleteSurfaceMessage,
    DataModelUpdateContent,
    DataModelUpdateMessage,
    DataEntry,
)


@dataclass
class SurfaceState:
    """State of an A2UI surface.

    Tracks components, data model, and rendering state for a surface.
    """
    surface_id: str
    catalog_id: str = "https://a2ui.dev/specification/0.8/standard_catalog.json"
    components: dict[str, A2UIComponent] = field(default_factory=dict)
    data_model: dict[str, Any] = field(default_factory=dict)
    root_id: Optional[str] = None
    is_rendering: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SurfaceManager:
    """Manages A2UI surface lifecycle.

    Provides methods to create, update, and delete surfaces while
    maintaining their state for incremental updates.
    """

    def __init__(self):
        """Initialize the SurfaceManager."""
        self._surfaces: dict[str, SurfaceState] = {}

    @property
    def surfaces(self) -> dict[str, SurfaceState]:
        """Get all active surfaces."""
        return self._surfaces

    def get(self, surface_id: str) -> Optional[SurfaceState]:
        """Get a surface by ID.

        Args:
            surface_id: Surface identifier

        Returns:
            SurfaceState or None if not found
        """
        return self._surfaces.get(surface_id)

    def exists(self, surface_id: str) -> bool:
        """Check if a surface exists.

        Args:
            surface_id: Surface identifier

        Returns:
            True if surface exists
        """
        return surface_id in self._surfaces

    def create(
        self,
        surface_id: str,
        catalog_id: str = "https://a2ui.dev/specification/0.8/standard_catalog.json",
    ) -> SurfaceState:
        """Create a new surface.

        Args:
            surface_id: Unique surface identifier
            catalog_id: Component catalog URI

        Returns:
            The created SurfaceState

        Raises:
            ValueError: If surface already exists
        """
        if surface_id in self._surfaces:
            raise ValueError(f"Surface '{surface_id}' already exists")

        state = SurfaceState(
            surface_id=surface_id,
            catalog_id=catalog_id,
        )
        self._surfaces[surface_id] = state
        return state

    def get_or_create(
        self,
        surface_id: str,
        catalog_id: str = "https://a2ui.dev/specification/0.8/standard_catalog.json",
    ) -> tuple[SurfaceState, bool]:
        """Get an existing surface or create a new one.

        Args:
            surface_id: Surface identifier
            catalog_id: Component catalog URI (used only if creating)

        Returns:
            Tuple of (SurfaceState, was_created)
        """
        if surface_id in self._surfaces:
            return self._surfaces[surface_id], False

        state = self.create(surface_id, catalog_id)
        return state, True

    def update_components(
        self,
        surface_id: str,
        components: list[A2UIComponent],
    ) -> SurfaceUpdateMessage:
        """Update components on a surface.

        Args:
            surface_id: Surface identifier
            components: Components to add or update

        Returns:
            SurfaceUpdateMessage for the client

        Raises:
            ValueError: If surface doesn't exist
        """
        state = self._surfaces.get(surface_id)
        if not state:
            raise ValueError(f"Surface '{surface_id}' not found")

        # Update component map
        for comp in components:
            state.components[comp.id] = comp

        state.updated_at = datetime.now()

        return SurfaceUpdateMessage(
            surfaceUpdate=SurfaceUpdateContent(
                surfaceId=surface_id,
                components=components,
            )
        )

    def begin_rendering(
        self,
        surface_id: str,
        root: str,
    ) -> BeginRenderingMessage:
        """Signal the client to begin rendering.

        Args:
            surface_id: Surface identifier
            root: ID of the root component

        Returns:
            BeginRenderingMessage for the client

        Raises:
            ValueError: If surface doesn't exist
        """
        state = self._surfaces.get(surface_id)
        if not state:
            raise ValueError(f"Surface '{surface_id}' not found")

        state.root_id = root
        state.is_rendering = True
        state.updated_at = datetime.now()

        return BeginRenderingMessage(
            beginRendering=BeginRenderingContent(
                surfaceId=surface_id,
                root=root,
                catalogId=state.catalog_id,
            )
        )

    def update_data(
        self,
        surface_id: str,
        data: dict[str, Any],
        path: Optional[str] = None,
    ) -> DataModelUpdateMessage:
        """Update the data model for a surface.

        Args:
            surface_id: Surface identifier
            data: Data to set
            path: Optional base path for the update

        Returns:
            DataModelUpdateMessage for the client

        Raises:
            ValueError: If surface doesn't exist
        """
        state = self._surfaces.get(surface_id)
        if not state:
            raise ValueError(f"Surface '{surface_id}' not found")

        # Update local data model
        if path:
            # Navigate to path and update
            self._set_at_path(state.data_model, path, data)
        else:
            state.data_model.update(data)

        state.updated_at = datetime.now()

        # Convert to A2UI format
        entries = [self._make_entry(k, v) for k, v in data.items()]

        return DataModelUpdateMessage(
            dataModelUpdate=DataModelUpdateContent(
                surfaceId=surface_id,
                path=path,
                contents=entries,
            )
        )

    def delete(self, surface_id: str) -> DeleteSurfaceMessage:
        """Delete a surface.

        Args:
            surface_id: Surface identifier

        Returns:
            DeleteSurfaceMessage for the client
        """
        self._surfaces.pop(surface_id, None)

        return DeleteSurfaceMessage(
            deleteSurface=DeleteSurfaceContent(
                surfaceId=surface_id,
            )
        )

    def clear(self) -> None:
        """Clear all surfaces."""
        self._surfaces.clear()

    def _set_at_path(self, data: dict, path: str, value: Any) -> None:
        """Set a value at a path in the data model."""
        parts = path.strip("/").split("/")
        current = data

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        if parts:
            current[parts[-1]] = value

    def _make_entry(self, key: str, value: Any) -> DataEntry:
        """Create a DataEntry from a Python value."""
        if isinstance(value, str):
            return DataEntry(key=key, valueString=value)
        elif isinstance(value, bool):
            return DataEntry(key=key, valueBoolean=value)
        elif isinstance(value, (int, float)):
            return DataEntry(key=key, valueNumber=float(value))
        elif isinstance(value, dict):
            nested = [self._make_entry(k, v) for k, v in value.items()]
            return DataEntry(key=key, valueMap=nested)
        elif isinstance(value, list):
            nested = [self._make_entry(str(i), v) for i, v in enumerate(value)]
            return DataEntry(key=key, valueList=nested)
        else:
            return DataEntry(key=key, valueString=str(value))


# Global instance for convenience
_default_manager: Optional[SurfaceManager] = None


def get_surface_manager() -> SurfaceManager:
    """Get the default SurfaceManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = SurfaceManager()
    return _default_manager
