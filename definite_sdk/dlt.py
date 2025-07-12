"""DLT (Data Load Tool) integration for Definite SDK."""

import os
import json
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import dlt
    from dlt.common import Destination
    from dlt.pipeline import Pipeline
else:
    try:
        import dlt
        from dlt.common import Destination
        from dlt.pipeline import Pipeline
    except ImportError:
        dlt = None  # type: ignore
        Destination = None  # type: ignore
        Pipeline = None  # type: ignore

from .client import DefiniteClient


class DefiniteDLTPipeline:
    """Wrapper for DLT pipelines with Definite state management."""

    def __init__(
        self,
        name: str,
        dataset_name: Optional[str] = None,
        destination: Optional["Destination"] = None,
        **kwargs: Any,
    ):
        """Initialize a DLT pipeline with Definite integration.

        Args:
            name: Pipeline name
            dataset_name: Dataset name for the destination
            destination: DLT destination (defaults to duckdb)
            **kwargs: Additional arguments passed to dlt.pipeline()
        """
        if dlt is None:
            raise ImportError(
                "dlt package not installed. Install with: pip install definite-sdk[dlt]"
            )

        self.name = name
        self._client = DefiniteClient()
        self._state_store = self._client.kv_store(f"dlt_state_{name}")

        # Default to DuckDB if no destination specified
        if destination is None:
            destination = "duckdb"

        # Use dataset_name or default to pipeline name
        if dataset_name is None:
            dataset_name = name

        # Create the underlying DLT pipeline
        self._pipeline = dlt.pipeline(
            pipeline_name=name,
            destination=destination,
            dataset_name=dataset_name,
            **kwargs,
        )

    @property
    def pipeline(self) -> "Pipeline":
        """Get the underlying DLT pipeline."""
        return self._pipeline

    @property
    def state(self) -> Dict[str, Any]:
        """Get the current pipeline state."""
        return dict(self._pipeline.state)

    def run(
        self,
        data: Any,
        *,
        table_name: Optional[str] = None,
        write_disposition: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Run the pipeline with the given data.

        Args:
            data: Data to load (resource, source, or iterator)
            table_name: Name of the table to load data into
            write_disposition: How to write data (append, replace, merge)
            **kwargs: Additional arguments passed to pipeline.run()

        Returns:
            Load info from the pipeline run
        """
        # Run the pipeline
        load_info = self._pipeline.run(
            data, table_name=table_name, write_disposition=write_disposition, **kwargs
        )

        # Persist state to Definite after successful run
        self._persist_state()

        return load_info

    def _persist_state(self) -> None:
        """Persist current pipeline state to Definite."""
        state = self._pipeline.state
        if state:
            # Store each state key separately for easier access
            for key, value in state.items():
                # Serialize value to JSON string
                self._state_store[key] = json.dumps(value)
            self._state_store.commit()

    def get_state(self, key: Optional[str] = None) -> Any:
        """Retrieve state from Definite store.

        Args:
            key: Specific state key to retrieve. If None, returns all state.

        Returns:
            State value or entire state dict
        """
        if key is not None:
            value = self._state_store.get(key, None)
            return json.loads(value) if value else None

        # Return all state as dict
        return {k: json.loads(self._state_store[k]) for k in self._state_store}

    def set_state(self, key: str, value: Any) -> None:
        """Set a state value.

        Args:
            key: State key
            value: State value
        """
        self._pipeline.state[key] = value
        # Also persist to Definite immediately
        self._state_store[key] = json.dumps(value)
        self._state_store.commit()

    def resume_from_state(self) -> None:
        """Resume pipeline from previously stored state."""
        # Load state from Definite
        stored_state: Dict[str, Any] = {
            k: json.loads(self._state_store[k]) for k in self._state_store
        }

        # Apply state to pipeline
        for key, value in stored_state.items():
            self._pipeline.state[key] = value

    def reset_state(self) -> None:
        """Reset pipeline state."""
        # Clear pipeline state
        self._pipeline.state.clear()

        # Clear Definite state
        keys_to_delete = list(self._state_store)
        for key in keys_to_delete:
            del self._state_store[key]
        self._state_store.commit()


class DLTStateAdapter:
    """Adapter for DLT state management conforming to Definite patterns."""

    def __init__(self, pipeline_name: str):
        """Initialize state adapter.

        Args:
            pipeline_name: Name of the DLT pipeline
        """
        self.pipeline_name = pipeline_name
        self._client = DefiniteClient()
        self._store = self._client.kv_store(f"dlt_state_{pipeline_name}")

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save pipeline state.

        Args:
            state: State dictionary to save
        """
        for key, value in state.items():
            self._store[key] = json.dumps(value)
        self._store.commit()

    def load_state(self) -> Dict[str, Any]:
        """Load pipeline state.

        Returns:
            State dictionary
        """
        return {k: json.loads(self._store[k]) for k in self._store}

    def clear_state(self) -> None:
        """Clear all state."""
        keys_to_delete = list(self._store)
        for key in keys_to_delete:
            del self._store[key]
        self._store.commit()


def get_duckdb_connection() -> Optional[Tuple[str, Any]]:
    """Get DuckDB connection from Definite integration.

    Uses the DEFINITE_API_KEY environment variable to authenticate and
    lookup the team's DuckDB integration.

    Returns:
        Optional[Tuple[str, Any]]: Tuple of (integration_id, connection) if found,
                                   None if no DuckDB integration or API key.
    """
    api_key = os.getenv("DEFINITE_API_KEY")
    if not api_key:
        return None

    try:
        import duckdb
    except ImportError:
        raise ImportError(
            "duckdb package not installed. Install with: pip install duckdb"
        )

    client = DefiniteClient(api_key=api_key)
    integration_store = client.integration_store()

    result = integration_store.lookup_duckdb_integration()
    if result:
        integration_id, connection_uri = result
        # Create DuckDB connection
        connection = duckdb.connect(connection_uri)
        return (integration_id, connection)

    return None
