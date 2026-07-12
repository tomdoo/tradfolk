import os
import uuid
from http import HTTPStatus

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel, ValidationError
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from .db import SessionLocal
from .models import Proposal, Vote, VoteValue

app = Flask(__name__)
secret_key = os.getenv("SECRET_KEY", "change-me")
app.config["SECRET_KEY"] = secret_key

allowed_origin = os.getenv("CORS_ORIGINS") or os.getenv("BASE_URL") or "https://tradfolk.local"
allowed_origin = allowed_origin.split(",", 1)[0].strip().rstrip("/")
CORS(app, resources={r"/*": {"origins": [allowed_origin]}}, supports_credentials=True)


def get_rate_limit_key() -> str:
    origin = getattr(g, "origin", None)
    if origin:
        return origin

    cookie_origin = deserialize_origin(request.cookies.get(ORIGIN_COOKIE_NAME))
    if cookie_origin:
        return cookie_origin

    header_origin = request.headers.get("X-Origin-Id", "").strip()
    if header_origin:
        try:
            return str(uuid.UUID(header_origin))
        except ValueError:
            pass

    return get_remote_address() or "unknown"


limiter = Limiter(
    key_func=get_rate_limit_key,
    app=app,
    storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"),
    default_limits=["240 per minute"],
)

origin_serializer = URLSafeSerializer(app.config["SECRET_KEY"], salt="origin-id")
ORIGIN_COOKIE_NAME = "tradfolk_origin"
ORIGIN_MAX_AGE_SECONDS = 60 * 60 * 24 * 365


class VotePayload(BaseModel):
    proposal_id: uuid.UUID
    value: VoteValue


def json_error(message: str, status: HTTPStatus):
    return jsonify({"error": message}), status


def deserialize_origin(raw_cookie: str | None) -> str | None:
    if not raw_cookie:
        return None
    try:
        payload = origin_serializer.loads(raw_cookie)
        candidate = payload.get("origin")
        uuid.UUID(str(candidate))
        return str(candidate)
    except (BadSignature, ValueError, AttributeError):
        return None


def serialize_origin(origin: str) -> str:
    return origin_serializer.dumps({"origin": origin})


def get_request_origin() -> str:
    cookie_origin = deserialize_origin(request.cookies.get(ORIGIN_COOKIE_NAME))
    if cookie_origin:
        return cookie_origin

    # Backward-compatible one-time migration from old client-generated header.
    header_origin = request.headers.get("X-Origin-Id", "").strip()
    if header_origin:
        try:
            parsed = str(uuid.UUID(header_origin))
            g.origin_cookie_to_set = parsed
            return parsed
        except ValueError:
            pass

    generated = str(uuid.uuid4())
    g.origin_cookie_to_set = generated
    return generated


@app.before_request
def attach_origin():
    g.origin_cookie_to_set = None
    g.origin = get_request_origin()


@app.after_request
def persist_origin_cookie(response):
    origin_to_set = getattr(g, "origin_cookie_to_set", None)
    if origin_to_set:
        response.set_cookie(
            ORIGIN_COOKIE_NAME,
            serialize_origin(origin_to_set),
            max_age=ORIGIN_MAX_AGE_SECONDS,
            httponly=True,
            secure=True,
            samesite="Lax",
            path="/",
        )
    return response


@app.errorhandler(ValidationError)
def handle_validation_error(_: ValidationError):
    return json_error("Payload invalide", HTTPStatus.BAD_REQUEST)


@app.errorhandler(429)
def handle_rate_limit(_):
    return json_error("Trop de requetes, reessaie dans un instant", HTTPStatus.TOO_MANY_REQUESTS)


@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception):
    if isinstance(error, HTTPException):
        return json_error(error.description, HTTPStatus(error.code))
    app.logger.exception("Unhandled error", exc_info=error)
    return json_error("Erreur serveur", HTTPStatus.INTERNAL_SERVER_ERROR)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/proposals/random")
@limiter.limit("60 per minute")
def get_random_proposal():
    origin = g.origin

    with SessionLocal() as session:
        already_voted = (
            select(Vote.id).where(Vote.id_proposal == Proposal.id, Vote.origin == origin).exists()
        )

        candidate = session.execute(
            select(Proposal)
            .where(Proposal.active.is_(True), ~already_voted)
            .order_by(func.random())
            .limit(1)
        ).scalar_one_or_none()

        if candidate is None:
            return jsonify({"message": "Plus de proposition disponible"}), 404

        return jsonify(
            {
                "id": str(candidate.id),
                "label": candidate.libelle,
                "image": candidate.image,
            }
        )


@app.get("/progress")
@limiter.limit("90 per minute")
def get_progress():
    origin = g.origin

    with SessionLocal() as session:
        total_proposals = (
            session.scalar(
                select(func.count()).select_from(Proposal).where(Proposal.active.is_(True))
            )
            or 0
        )
        voted_proposals = (
            session.scalar(
                select(func.count())
                .select_from(Vote)
                .join(Proposal, Proposal.id == Vote.id_proposal)
                .where(Vote.origin == origin, Proposal.active.is_(True))
            )
            or 0
        )

        return jsonify(
            {
                "voted": voted_proposals,
                "total": total_proposals,
                "remaining": max(total_proposals - voted_proposals, 0),
            }
        )


@app.post("/votes")
@limiter.limit("30 per minute")
def create_vote():
    origin = g.origin

    payload = VotePayload.model_validate(request.get_json(silent=True) or {})
    pid = payload.proposal_id

    with SessionLocal() as session:
        p = session.get(Proposal, pid)
        if not p or not p.active:
            return json_error("Proposition introuvable", HTTPStatus.NOT_FOUND)

        session.add(Vote(id_proposal=pid, value=payload.value, origin=origin))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return json_error("Deja vote pour cette proposition", HTTPStatus.CONFLICT)

        stats_row = session.execute(
            select(
                func.coalesce(
                    func.sum(case((Vote.value == VoteValue.trad, 1), else_=0)),
                    0,
                ).label("trad"),
                func.coalesce(
                    func.sum(case((Vote.value == VoteValue.folk, 1), else_=0)),
                    0,
                ).label("folk"),
            ).where(Vote.id_proposal == pid)
        ).one()

        trad = int(stats_row.trad)
        folk = int(stats_row.folk)
        total = trad + folk

        return jsonify(
            {
                "proposal_id": str(pid),
                "counts": {"trad": trad, "folk": folk, "total": total},
                "percentages": {
                    "trad": round((trad / total) * 100, 2) if total else 0,
                    "folk": round((folk / total) * 100, 2) if total else 0,
                },
            }
        )


@app.get("/results")
@limiter.limit("60 per minute")
def get_results():
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Proposal.id,
                Proposal.libelle,
                Proposal.image,
                Proposal.active,
                func.coalesce(
                    func.sum(case((Vote.value == VoteValue.trad, 1), else_=0)),
                    0,
                ).label("trad"),
                func.coalesce(
                    func.sum(case((Vote.value == VoteValue.folk, 1), else_=0)),
                    0,
                ).label("folk"),
            )
            .outerjoin(Vote, Vote.id_proposal == Proposal.id)
            .group_by(Proposal.id)
            .order_by(Proposal.libelle.asc())
        ).all()

        results = []
        for row in rows:
            trad = int(row.trad)
            folk = int(row.folk)
            total = trad + folk
            results.append(
                {
                    "id": str(row.id),
                    "label": row.libelle,
                    "image": row.image,
                    "active": row.active,
                    "counts": {"trad": trad, "folk": folk, "total": total},
                    "percentages": {
                        "trad": round((trad / total) * 100, 2) if total else 0,
                        "folk": round((folk / total) * 100, 2) if total else 0,
                    },
                }
            )
        return jsonify(results)
