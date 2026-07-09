import json
import uuid
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from .db import SessionLocal
from .models import Proposal

JSON_PATH = Path("/app/data/proposals.json")


class ProposalImportItem(BaseModel):
    id: uuid.UUID
    label: str = Field(min_length=1, max_length=255)
    image: str = Field(min_length=1, max_length=1024)
    active: bool = True


def resolve_json_path() -> Path | None:
    if not JSON_PATH.exists():
        return None

    if JSON_PATH.is_file():
        return JSON_PATH

    if JSON_PATH.is_dir():
        # Accept common layouts when a directory is mounted accidentally or by design.
        candidates = [
            JSON_PATH / "proposals.json",
            JSON_PATH / "data.json",
        ]
        candidates.extend(sorted(JSON_PATH.glob("*.json")))
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    return None


def run():
    source_path = resolve_json_path()
    if not source_path:
        print("No proposals.json found, skipping import.")
        return

    try:
        raw_data = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON in {source_path}: {error}") from error

    if not isinstance(raw_data, list):
        raise RuntimeError("Import payload must be a JSON array of proposals")

    parsed_items: list[ProposalImportItem] = []
    seen_ids: set[uuid.UUID] = set()
    for index, raw_item in enumerate(raw_data, start=1):
        try:
            item = ProposalImportItem.model_validate(raw_item)
        except ValidationError as error:
            raise RuntimeError(f"Invalid proposal at row {index}: {error}") from error

        if item.id in seen_ids:
            raise RuntimeError(f"Duplicate proposal id found in import file: {item.id}")
        seen_ids.add(item.id)
        parsed_items.append(item)

    with SessionLocal() as session:
        for item in parsed_items:
            row = session.get(Proposal, item.id)
            if row:
                row.libelle = item.label
                row.image = item.image
                row.active = item.active
            else:
                session.add(
                    Proposal(
                        id=item.id,
                        libelle=item.label,
                        image=item.image,
                        active=item.active,
                    )
                )
        session.commit()
    print(f"Imported {len(parsed_items)} proposals")


if __name__ == "__main__":
    run()
