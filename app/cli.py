#!/usr/bin/env python3
"""FastStarter project CLI — stdlib argparse (no extra CLI library).

From the project root (venv active, deps installed; ``.env`` optional — falls back to ``.env.example``):

    python manage.py init
    python manage.py run
    python manage.py users
    python manage.py report --name "Student Name" --id "816000000"
    python manage.py usecase
    python manage.py skills-verify
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_models_loaded() -> None:
    import app.models  # noqa: F401


def cmd_init(args: argparse.Namespace) -> None:
    """Create database tables (drops existing by default) and seed demo users."""
    from app.config import get_settings
    from app.database import drop_all, ensure_db_and_tables

    _ensure_models_loaded()
    if args.drop:
        print("Dropping all tables…")
        # Drop can fail on a brand-new empty DB; create path still retries.
        try:
            drop_all()
        except Exception as exc:  # noqa: BLE001
            from app.database import is_db_not_ready_error

            if not is_db_not_ready_error(exc):
                raise
            print(f"Database not ready yet while dropping ({exc}); continuing…")
    print("Creating tables…")
    ensure_db_and_tables()
    print(f"Database ready ({get_settings().database_uri}).")
    if getattr(args, "seed", True):
        cmd_seed(args)


def cmd_seed(args: argparse.Namespace) -> None:
    """Insert demo users.

    bob / bobpass       (regular_user)
    admin / adminpass   (admin)
    """
    from app.database import ensure_db_and_tables, get_cli_session
    from app.repositories.user import UserRepository
    from app.schemas.user import AdminCreate, RegularUserCreate
    from app.utilities.security import encrypt_password

    _ensure_models_loaded()
    ensure_db_and_tables()

    demo_users = [
        ("bob", "bob@example.com", "bobpass", "+1 868 555 0101", "regular_user", "The University of the West Indies"),
        ("admin", "admin@example.com", "adminpass", "+1 868 555 0102", "admin", "N/A"),
        ("host", "host@example.com", "hostpass", "+1 868 555 0103", "host", "N/A"),
        ("dana", "dana@example.com", "danapass", "+1 868 555 0105", "regular_user", "The University of the West Indies"),
    ]

    created = 0
    skipped = 0
    with get_cli_session() as session:
        repo = UserRepository(session)
        for username, email, password, phone, role, university in demo_users:
            if repo.get_by_username(username):
                print(f"  skip  {username} (already exists)")
                skipped += 1
                continue
            payload_cls = AdminCreate if role == "admin" else RegularUserCreate
            repo.create(
                payload_cls(
                    username=username,
                    email=email,
                    password=encrypt_password(password),
                    phone=phone,
                    role=role,
                    university=university,
                )
            )
            print(f"  create {username} ({role})")
            created += 1

    print(f"Seed done — created {created}, skipped {skipped}.")

    # Demo listings for Explore (owned by the seeded host).
    from decimal import Decimal

    from sqlmodel import select

    from app.models.listing import Listing
    from app.models.listing_image import ListingImage

    # Each demo listing gets its own set of free-to-use stock photos (Unsplash License).
    # Files live in app/static/img/listings/ so they serve locally in dev and on Render.
    demo_listings = [
        ("Sunlit Room near UWI", "St. Augustine", 1, 1800, 5, "Bright single room, 5 min walk to campus.", "sunlit-room"),
        ("Shared Flat on Eastern Rd", "St. Augustine", 2, 1450, 12, "Two-bed flat share with wifi and parking.", "shared-flat"),
        ("Quiet Studio, Mount Hope", "Mount Hope", 1, 2100, 6, "Self-contained studio next to the medical campus.", "quiet-studio"),
        ("Garden Cottage, St. Aug.", "St. Augustine", 3, 3200, 12, "Private cottage with garden and kitchen.", "garden-cottage"),
    ]
    photos_per_listing = 3

    def listing_photo_urls(slug: str) -> list[str]:
        return [
            f"/static/img/listings/{slug}-{i}.jpg"
            for i in range(1, photos_per_listing + 1)
        ]

    with get_cli_session() as session:
        host_user = UserRepository(session).get_by_username("host")
        existing = session.exec(select(Listing)).all()
        if host_user and not existing:
            for title, loc, cap, rent, months, desc, slug in demo_listings:
                listing = Listing(
                    host_id=host_user.user_id,
                    title=title,
                    location=loc,
                    capacity=cap,
                    monthly_rent=Decimal(rent),
                    duration_months=months,
                    description=desc,
                )
                session.add(listing)
                session.flush()  # get listing_id for the images
                for i, url in enumerate(listing_photo_urls(slug)):
                    session.add(
                        ListingImage(
                            listing_id=listing.listing_id,
                            image_url=url,
                            caption=f"{title} — photo {i + 1}",
                        )
                    )
            session.commit()
            print(f"  created {len(demo_listings)} demo listings (host) with photos")

    # A pending reservation for the host to approve (workflow2 demo data).
    from app.models.reservation import Reservation, ReservationStatus

    with get_cli_session() as session:
        student = UserRepository(session).get_by_username("bob")
        listing = session.exec(select(Listing).order_by(Listing.listing_id)).first()
        has_reservation = session.exec(select(Reservation)).first()
        if student and listing and not has_reservation:
            # Minimal 1x1 PNG so the proof link opens a real file.
            png = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
                b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            session.add(
                Reservation(
                    user_id=student.user_id,
                    listing_id=listing.listing_id,
                    proof_filename="proof-of-enrollment.png",
                    proof_content_type="image/png",
                    proof_data=png,
                )
            )
            session.commit()
            print(f"  created 1 pending reservation (bob → listing {listing.listing_id})")

    # Reviews demo data (student decision: reviews are seeded, not authored in
    # the UI — the assignment demo does not need a "write a review" screen).
    #
    # Phase 3 rule: only an APPROVED reservation may produce a review, so every
    # row below hangs off an approved (and accepted) reservation. Dana is a
    # second student so bob's own path stays clean — he can still walk listing 1
    # from pending → approved → accepted, and reserve fresh on 2, 3 and 4.
    #
    # Capacities are respected so no listing reads as full for the demo:
    #   listing 1 cap 1 — bob's live pending reservation (untouched)
    #   listing 2 cap 2 — dana holds 1, 1 slot left for bob
    #   listing 3 cap 1 — untouched, bob can reserve it
    #   listing 4 cap 3 — dana holds 1, 2 slots left for bob
    from app.models.review import Review
    from datetime import datetime as _dt

    demo_reviews = {
        "shared-flat": [
            ("Great location, five minutes from the library. The wifi never dropped once.",
             "2026-09-14"),
            ("Cooked for myself the whole stay — the kitchen is bigger than it looks in the photos.",
             "2026-09-20"),
        ],
        "garden-cottage": [
            ("Quietest place I have stayed near campus. The garden is a proper retreat during exams.",
             "2026-08-02"),
            ("Host sorted the meter and the internet within a day of me asking. No complaints.",
             "2026-08-11"),
        ],
    }

    with get_cli_session() as session:
        dana = UserRepository(session).get_by_username("dana")
        by_title = {listing.title: listing for listing in session.exec(select(Listing)).all()}
        # demo_listings rows are (title, location, capacity, rent, months, description, slug)
        by_slug = {slug: by_title.get(title) for title, _, _, _, _, _, slug in demo_listings}
        existing_reviews = session.exec(select(Review)).first()
        if dana and not existing_reviews:
            # Minimal 1x1 PNG so Dana's proof link opens a real file. Defined
            # here rather than reused: the block above only binds its copy when
            # bob's reservation is actually created.
            proof_png = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
                b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            created = 0
            for slug, entries in demo_reviews.items():
                listing = by_slug.get(slug)
                if listing is None:
                    continue
                # One reservation per (student, listing) — approved and accepted,
                # which is what makes a review legal under the Phase 3 rule.
                reservation = Reservation(
                    user_id=dana.user_id,
                    listing_id=listing.listing_id,
                    proof_filename="proof-of-enrollment.png",
                    proof_content_type="image/png",
                    proof_data=proof_png,
                    status=ReservationStatus.APPROVED,
                    confirmed_at=_dt(2026, 8, 1, 10, 0),
                )
                session.add(reservation)
                session.flush()
                for comment, day in entries:
                    session.add(
                        Review(
                            reservation_id=reservation.reservation_id,
                            comment=comment,
                            created_at=_dt.fromisoformat(f"{day}T12:00"),
                        )
                    )
                    created += 1
            session.commit()
            print(f"  created {created} seeded reviews (dana, approved stays)")

    # A pending host applicant for the admin to approve (workflow3 demo data).
    from datetime import datetime

    from app.models.user import HOST_ACCOUNT_STATUS
    from app.schemas.user import HostCreate

    with get_cli_session() as session:
        repo = UserRepository(session)
        if not repo.get_by_username("cara"):
            # Cara's face photo is a real local JPEG (Unsplash License), served
            # to the admin from the DB blob via /admin/applicants/{id}/face —
            # the same local-file approach as the listing photos, so it works
            # offline and on Render. Falls back to a 1x1 PNG if the asset is
            # ever missing, so the seed never hard-crashes.
            from pathlib import Path

            face_path = Path(__file__).resolve().parent / "static" / "img" / "faces" / "cara.jpg"
            face_bytes = face_path.read_bytes() if face_path.is_file() else (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
                b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            face_is_jpeg = face_path.is_file()
            # A tiny PDF so the admin card's credentials link opens a real file.
            pdf = (
                b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
                b"trailer<</Root 1 0 R>>\n%%EOF"
            )
            repo.create(
                HostCreate(
                    username="cara",
                    email="cara@example.com",
                    password=encrypt_password("carapass"),
                    role="host",
                    phone="+1 868 555 0104",
                    university="The University of the West Indies",
                    status=HOST_ACCOUNT_STATUS.PENDING,
                    applied_at=datetime.today(),
                    face_filename="cara.jpg" if face_is_jpeg else "cara-face.png",
                    face_content_type="image/jpeg" if face_is_jpeg else "image/png",
                    face_data=face_bytes,
                    credentials_filename="cara-credentials.pdf",
                    credentials_content_type="application/pdf",
                    credentials_data=pdf,
                )
            )
            print("  create cara (pending host applicant — approve her as admin)")
    print("Login with bob/bobpass, host/hostpass or admin/adminpass")


def cmd_run(args: argparse.Namespace) -> None:
    """Start the FastAPI app with Uvicorn."""
    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    bind_host = args.host or settings.app_host
    bind_port = args.port or settings.app_port
    if args.reload is None:
        use_reload = settings.env.lower() != "production"
    else:
        use_reload = args.reload
    print(f"Starting FastStarter on http://{bind_host}:{bind_port} (reload={use_reload})")
    uvicorn.run(
        "app.main:app",
        host=bind_host,
        port=bind_port,
        reload=use_reload,
    )


def cmd_report(args: argparse.Namespace) -> None:
    """Build the submission package: merge judge, package transcripts, write PDF.

    Guide must (1) write ``docs/judge.md`` and (2) pull every Guide chat into
    ``docs/transcripts/*.md`` before this command. Report only packages those files.
    """
    from app.report_pdf import export_report
    from app.skill_integrity import format_report, verify

    result = export_report(
        name=args.name,
        student_id=args.student_id,
        source=None if args.src is None else Path(args.src),
        output=None if args.output is None else Path(args.output),
        include_appendix=args.with_appendix,
    )
    print()
    print("Report package:")
    print(
        f"  Judge:       {'merged docs/judge.md' if result.judge_merged else 'MISSING - Guide must run student-judge first'}"
    )
    print(
        f"  Transcripts: {result.transcript_count} chat(s) in docs/transcripts/"
        + (
            ""
            if result.transcript_count
            else " (EMPTY - Guide must pull Copilot/Cursor/OpenCode chats first)"
        )
    )
    if result.transcript_zip:
        print(f"  Zip:         {result.transcript_zip.as_posix()}")
    print(f"  PDF:         {result.pdf_path.as_posix()}")
    print(format_report(verify()))


def cmd_transcripts(args: argparse.Namespace) -> None:
    """Package agent-written markdown under docs/transcripts/ (+ zip)."""
    from app.transcript_export import package_transcripts

    result = package_transcripts(make_zip=not args.no_zip)
    if result.found == 0:
        print(
            "Warning: no chat markdown in docs/transcripts/. "
            "The Guide agent must pull every Guide chat for this project "
            "(Copilot Agent, Cursor, or OpenCode) into docs/transcripts/<slug>.md first."
        )
        raise SystemExit(2)
    print(f"Submission package ready: {result.out_dir}")
    if result.zip_path:
        print(f"Zip for submission: {result.zip_path}")


def cmd_skills_verify(args: argparse.Namespace) -> None:
    """Check course skill files against .agents/skills.lock.json."""
    from app.skill_integrity import format_report, verify

    result = verify()
    print(format_report(result))
    if not result.ok:
        raise SystemExit(1)


def cmd_usecase(args: argparse.Namespace) -> None:
    """Render docs/diagrams/use-case.json to a UML use-case PNG."""
    from app.usecase_diagram import render_usecase_png

    dest = render_usecase_png(
        spec_path=None if args.spec is None else Path(args.spec),
        output=None if args.output is None else Path(args.output),
    )
    print(f"Wrote {dest}")


def cmd_skills_lock(args: argparse.Namespace) -> None:
    """Rewrite the skill lockfile (course authors only)."""
    from app.skill_integrity import write_lock

    dest = write_lock()
    print(f"Wrote {dest}")


def cmd_users(args: argparse.Namespace) -> None:
    """List users currently in the database."""
    from sqlmodel import select

    from app.database import get_cli_session
    from app.models.user import User

    _ensure_models_loaded()
    with get_cli_session() as session:
        users = session.exec(select(User)).all()
        if not users:
            print("No users found. Run: python manage.py init")
            return
        for user in users:
            print(
                f"  id={user.user_id}  username={user.username}  "
                f"role={user.role}  email={user.email}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python manage.py",
        description="FastStarter Python CLI — init database, seed demo data, run the app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create DB tables and seed demo users (drops existing tables by default)",
    )
    p_init.add_argument(
        "--no-drop",
        dest="drop",
        action="store_false",
        help="Create tables without dropping existing ones",
    )
    p_init.add_argument(
        "--no-seed",
        dest="seed",
        action="store_false",
        help="Skip demo user seed after creating tables",
    )
    p_init.set_defaults(drop=True, seed=True, func=cmd_init)

    p_seed = sub.add_parser(
        "seed",
        help="Insert demo users only (idempotent; also runs as part of init)",
    )
    p_seed.set_defaults(func=cmd_seed)

    p_run = sub.add_parser("run", help="Start the web app (uvicorn)")
    p_run.add_argument("--host", default=None, help="Bind host")
    p_run.add_argument("--port", type=int, default=None, help="Bind port")
    reload_group = p_run.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload", dest="reload", action="store_true", default=None, help="Enable auto-reload"
    )
    reload_group.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Disable auto-reload"
    )
    p_run.set_defaults(func=cmd_run, reload=None)

    p_users = sub.add_parser("users", help="List users in the database")
    p_users.set_defaults(func=cmd_users)

    p_report = sub.add_parser(
        "report",
        help=(
            "Build submission package: merge docs/judge.md, package docs/transcripts/, "
            "write docs/report.pdf (Guide pulls chats + runs student-judge first)"
        ),
    )
    p_report.add_argument("--name", required=True, help="Student name (printed on the PDF cover)")
    p_report.add_argument("--id", dest="student_id", required=True, help="Student ID (PDF only)")
    p_report.add_argument("--src", default=None, help="Markdown path (default: docs/report.md)")
    p_report.add_argument("--output", default=None, help="PDF path (default: docs/report.pdf)")
    p_report.add_argument(
        "--with-appendix",
        action="store_true",
        help="Also append the full session transcripts to the PDF (default: leave them out)",
    )
    p_report.set_defaults(func=cmd_report)

    p_transcripts = sub.add_parser(
        "transcripts",
        help="Package agent-written docs/transcripts/*.md into INDEX + zip (no IDE scrape)",
    )
    p_transcripts.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip writing docs/transcripts.zip",
    )
    p_transcripts.set_defaults(func=cmd_transcripts)

    p_usecase = sub.add_parser(
        "usecase",
        help="Render docs/diagrams/use-case.json to a UML use-case PNG",
    )
    p_usecase.add_argument("--spec", default=None, help="JSON spec (default: docs/diagrams/use-case.json)")
    p_usecase.add_argument("--output", default=None, help="PNG path (default: docs/diagrams/use-case.png)")
    p_usecase.set_defaults(func=cmd_usecase)

    p_skills_verify = sub.add_parser(
        "skills-verify",
        help="Check course skills against .agents/skills.lock.json",
    )
    p_skills_verify.set_defaults(func=cmd_skills_verify)

    p_skills_lock = sub.add_parser(
        "skills-lock",
        help="Rewrite .agents/skills.lock.json (course authors; needs FASTSTARTER_SKILLS_LOCK=1)",
    )
    p_skills_lock.set_defaults(func=cmd_skills_lock)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
