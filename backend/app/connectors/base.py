from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveredColumn:
    name: str
    data_type: str
    ordinal_position: int
    nullable: bool


@dataclass(frozen=True)
class DiscoveredAsset:
    name: str
    source_path: str
    asset_type: str
    schema_name: str | None
    row_count: int
    columns: list[DiscoveredColumn]


@dataclass(frozen=True)
class DiscoveredSchema:
    name: str
    asset_names: list[str]


class BaseConnector:
    def test(self) -> dict:
        raise NotImplementedError

    def discover_schemas(self) -> list[DiscoveredSchema]:
        raise NotImplementedError

    def discover_assets(self, scope: dict | None = None) -> list[DiscoveredAsset]:
        raise NotImplementedError
