import os
from pathlib import Path
import pytest
from dotenv import load_dotenv
import pyTigerGraph as tg

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

@pytest.fixture(scope="session")
def tg_conn():
    conn = tg.TigerGraphConnection(
        host=os.getenv("TG_HOST", "http://localhost"),
        restppPort=int(os.getenv("TG_PORT", "14240")),
        username=os.getenv("TG_USERNAME", "tigergraph"),
        password=os.getenv("TG_PASSWORD", "tigergraph"),
        graphname=os.getenv("TG_GRAPH_NAME", "FraudInvestigation"),
    )
    return conn

@pytest.fixture(scope="session")
def root_dir():
    return project_root
