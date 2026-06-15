from __future__ import annotations

import json
from pathlib import Path

from models.availability import DailyBlock


class DailyBlockStorage:
    def __init__(self, path: Path = Path("data/daily_blocks.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_raw([])

    def get_all(self) -> list[DailyBlock]:
        return [DailyBlock.model_validate(item) for item in self._read_raw()]

    def get_by_id(self, block_id: str) -> DailyBlock | None:
        for block in self.get_all():
            if block.id == block_id:
                return block
        return None

    def save_all(self, blocks: list[DailyBlock]) -> None:
        self._write_raw([block.model_dump(mode="json") for block in blocks])

    def add(self, block: DailyBlock) -> DailyBlock:
        blocks = self.get_all()
        blocks.append(block)
        self.save_all(blocks)
        return block

    def update(self, updated_block: DailyBlock) -> DailyBlock:
        blocks = self.get_all()
        for index, block in enumerate(blocks):
            if block.id == updated_block.id:
                blocks[index] = updated_block
                self.save_all(blocks)
                return updated_block
        raise LookupError("Daily block not found")

    def delete(self, block_id: str) -> None:
        blocks = self.get_all()
        remaining_blocks = [block for block in blocks if block.id != block_id]
        if len(remaining_blocks) == len(blocks):
            raise LookupError("Daily block not found")
        self.save_all(remaining_blocks)

    def _read_raw(self) -> list[dict]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _write_raw(self, data: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
