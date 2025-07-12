"""Integration tests for DLT with DuckDB."""

import os
import tempfile
from pathlib import Path
import pytest

# Skip tests if required packages not installed
dlt = pytest.importorskip("dlt")
duckdb = pytest.importorskip("duckdb")

from definite_sdk.dlt import DefiniteDLTPipeline, DLTStateAdapter


@pytest.fixture
def temp_duckdb():
    """Create a temporary DuckDB database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_dlt_pipeline_with_duckdb(temp_duckdb):
    """Test end-to-end DLT pipeline with DuckDB."""
    # Skip if no API key
    if not os.getenv("DEF_API_KEY"):
        pytest.skip("DEF_API_KEY not set")

    # Create a simple incremental resource
    @dlt.resource(primary_key="id", write_disposition="merge")
    def orders(cursor=dlt.sources.incremental("created_at")):
        # Simulate data with cursor
        last_value = cursor.last_value or "2024-01-01"

        # Generate sample data
        data = [
            {"id": 1, "amount": 100.0, "created_at": "2024-01-01"},
            {"id": 2, "amount": 200.0, "created_at": "2024-01-02"},
            {"id": 3, "amount": 300.0, "created_at": "2024-01-03"},
        ]

        # Filter based on cursor
        for order in data:
            if order["created_at"] > last_value:
                yield order

    # Create pipeline
    pipeline = DefiniteDLTPipeline(
        "test_orders", destination=dlt.destinations.duckdb(credentials=temp_duckdb)
    )

    # First run - should load all data
    info1 = pipeline.run(orders())
    assert info1.loads_ids is not None

    # Check state was persisted
    state = pipeline.get_state()
    assert "orders" in state
    assert state["orders"]["incremental"]["created_at"]["last_value"] == "2024-01-03"

    # Verify data in DuckDB
    conn = duckdb.connect(temp_duckdb)
    result = conn.execute("SELECT COUNT(*) FROM test_orders.orders").fetchone()
    assert result[0] == 3

    # Second run - should load no new data
    info2 = pipeline.run(orders())

    # Verify count hasn't changed
    result = conn.execute("SELECT COUNT(*) FROM test_orders.orders").fetchone()
    assert result[0] == 3

    conn.close()


def test_dlt_state_persistence(temp_duckdb):
    """Test state persistence across pipeline instances."""
    if not os.getenv("DEF_API_KEY"):
        pytest.skip("DEF_API_KEY not set")

    @dlt.resource(primary_key="id")
    def items():
        yield from [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
        ]

    # Create and run first pipeline
    pipeline1 = DefiniteDLTPipeline(
        "test_persistence", destination=dlt.destinations.duckdb(credentials=temp_duckdb)
    )

    # Set custom state
    pipeline1.set_state("custom_key", "custom_value")
    pipeline1.set_state("counter", 42)

    # Run pipeline
    pipeline1.run(items())

    # Create new pipeline instance with same name
    pipeline2 = DefiniteDLTPipeline(
        "test_persistence", destination=dlt.destinations.duckdb(credentials=temp_duckdb)
    )

    # Resume from state
    pipeline2.resume_from_state()

    # Verify state was restored
    assert pipeline2.get_state("custom_key") == "custom_value"
    assert pipeline2.get_state("counter") == 42


def test_dlt_state_adapter():
    """Test DLTStateAdapter functionality."""
    if not os.getenv("DEF_API_KEY"):
        pytest.skip("DEF_API_KEY not set")

    adapter = DLTStateAdapter("test_adapter")

    # Save state
    test_state = {"cursor": "2024-01-15", "offset": 1000, "status": "running"}
    adapter.save_state(test_state)

    # Load state
    loaded_state = adapter.load_state()
    assert loaded_state == test_state

    # Clear state
    adapter.clear_state()
    cleared_state = adapter.load_state()
    assert cleared_state == {}


def test_pipeline_state_management():
    """Test pipeline state management operations."""
    if not os.getenv("DEF_API_KEY"):
        pytest.skip("DEF_API_KEY not set")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        pipeline = DefiniteDLTPipeline(
            "test_state_mgmt", destination=dlt.destinations.duckdb(credentials=db_path)
        )

        # Test setting and getting state
        pipeline.set_state("key1", "value1")
        pipeline.set_state("key2", {"nested": "data"})

        assert pipeline.get_state("key1") == "value1"
        assert pipeline.get_state("key2") == {"nested": "data"}

        # Test getting all state
        all_state = pipeline.get_state()
        assert "key1" in all_state
        assert "key2" in all_state

        # Test reset
        pipeline.reset_state()
        assert pipeline.get_state() == {}

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
