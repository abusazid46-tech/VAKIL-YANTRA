import json
from pathlib import Path
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import ActSection, Firm, LegalSource, Matter, Membership, User
from app.db.session import SessionLocal


def seed_development_data() -> None:
    db = SessionLocal()
    try:
        # 1. Seed demo firm & users if absent
        if not db.scalar(select(Firm).where(Firm.id == "firm_vakil_demo")):
            firm = Firm(id="firm_vakil_demo", name="Vakil Yantra Demo Chamber", plan="chamber")
            admin = User(
                id="usr_admin",
                email="advocate@vakilyantra.in",
                name="A. Sharma",
                password_hash=hash_password("Vakil@123"),
            )
            associate = User(
                id="usr_associate",
                email="associate@vakilyantra.in",
                name="Priya Counsel",
                password_hash=hash_password("Associate@123"),
            )
            db.add_all([firm, admin, associate])
            db.flush()
            db.add_all(
                [
                    Membership(id="mem_admin", firm_id=firm.id, user_id=admin.id, role="admin_advocate"),
                    Membership(id="mem_associate", firm_id=firm.id, user_id=associate.id, role="advocate"),
                    Matter(
                        id="mat_ni_138",
                        firm_id=firm.id,
                        title="Rahman v. Barua Traders",
                        court="District Court, Kamrup",
                        matter_type="NI Act S.138",
                        client_name="M. Rahman",
                        next_action="Draft rejoinder and verify service proof",
                        created_by=admin.id,
                    ),
                    Matter(
                        id="mat_bail_001",
                        firm_id=firm.id,
                        title="State v. Ajit Deka",
                        court="Gauhati High Court",
                        matter_type="Bail",
                        client_name="Ajit Deka",
                        next_action="Upload certified FIR copy",
                        created_by=admin.id,
                    ),
                ]
            )
            db.commit()

        # 2. Seed core statutory sources
        core_sources = [
            LegalSource(
                id="src_constitution",
                title="Constitution of India",
                act_number="Constituent Assembly",
                enactment_date="1950-01-26",
                source_type="act",
                jurisdiction="India",
                year=1950,
                public_url="https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Constitution+of+India",
                effective_status="current",
            ),
            LegalSource(
                id="src_bns_2023",
                title="Bharatiya Nyaya Sanhita, 2023",
                act_number="45 of 2023",
                enactment_date="2023-12-25",
                source_type="act",
                jurisdiction="India",
                year=2023,
                public_url="https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Bharatiya+Nyaya+Sanhita",
                effective_status="current",
            ),
            LegalSource(
                id="src_bnss_2023",
                title="Bharatiya Nagarik Suraksha Sanhita, 2023",
                act_number="46 of 2023",
                enactment_date="2023-12-25",
                source_type="act",
                jurisdiction="India",
                year=2023,
                public_url="https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Bharatiya+Nagarik+Suraksha+Sanhita",
                effective_status="current",
            ),
            LegalSource(
                id="src_bsa_2023",
                title="Bharatiya Sakshya Adhiniyam, 2023",
                act_number="47 of 2023",
                enactment_date="2023-12-25",
                source_type="act",
                jurisdiction="India",
                year=2023,
                public_url="https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Bharatiya+Sakshya+Adhiniyam",
                effective_status="current",
            ),
            LegalSource(
                id="src_limitation_1963",
                title="Limitation Act, 1963",
                act_number="36 of 1963",
                enactment_date="1963-10-05",
                source_type="act",
                jurisdiction="India",
                year=1963,
                public_url="https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Limitation+Act",
                effective_status="current",
            ),
            LegalSource(
                id="src_ni_1881",
                title="Negotiable Instruments Act, 1881",
                act_number="26 of 1881",
                enactment_date="1881-12-09",
                source_type="act",
                jurisdiction="India",
                year=1881,
                public_url="https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Negotiable+Instruments+Act",
                effective_status="current",
            ),
        ]
        for src in core_sources:
            if not db.scalar(select(LegalSource).where(LegalSource.id == src.id)):
                db.add(src)
        db.commit()

        # 3. Seed Central Acts Catalog (~600 Central Acts)
        catalog_path = Path(__file__).resolve().parent / "central_acts_catalog.json"
        if catalog_path.exists():
            existing_act_ids = set(db.scalars(select(LegalSource.id)).all())
            with open(catalog_path, encoding="utf-8") as f:
                catalog = json.load(f)
            new_sources = []
            for item in catalog:
                if item["id"] not in existing_act_ids:
                    new_sources.append(
                        LegalSource(
                            id=item["id"],
                            title=item["title"],
                            act_number=str(item.get("act_number", "")),
                            enactment_date=str(item.get("enactment_date", "")),
                            source_type=item.get("source_type", "central_act"),
                            jurisdiction=item.get("jurisdiction", "India"),
                            year=int(item.get("year", 2024)),
                            public_url=item.get("public_url", "https://www.indiacode.nic.in/"),
                            effective_status=item.get("effective_status", "current"),
                        )
                    )
                    existing_act_ids.add(item["id"])
            if new_sources:
                db.add_all(new_sources)
                db.commit()

        # 4. Seed active statutory sections for RAG
        consolidated_path = Path(__file__).resolve().parent / "extracted_acts" / "consolidated_rag_sections.json"
        sections_path = Path(__file__).resolve().parent / "statutory_sections.json"
        
        target_files = []
        if consolidated_path.exists():
            target_files.append(consolidated_path)
        if sections_path.exists():
            target_files.append(sections_path)

        existing_section_ids = set(db.scalars(select(ActSection.id)).all())
        new_sections = []
        for tf in target_files:
            with open(tf, encoding="utf-8") as f:
                sections_data = json.load(f)
            for sec in sections_data:
                if sec["id"] not in existing_section_ids:
                    new_sections.append(
                        ActSection(
                            id=sec["id"],
                            act_id=sec.get("act_id", "act_statutory"),
                            act_title=sec.get("act_title", "Central Act"),
                            chapter=sec.get("chapter"),
                            section_number=str(sec.get("section_number", "1")),
                            section_title=sec.get("section_title", "Section"),
                            content=sec.get("content", ""),
                            chunk_type=sec.get("chunk_type", "section"),
                            source_url=sec.get("source_url", "https://www.indiacode.nic.in/"),
                        )
                    )
                    existing_section_ids.add(sec["id"])
        if new_sections:
            batch_size = 1000
            for i in range(0, len(new_sections), batch_size):
                batch = new_sections[i : i + batch_size]
                db.add_all(batch)
                db.commit()
                print(f"Seeded sections: {min(i + batch_size, len(new_sections))} / {len(new_sections)}", flush=True)

    finally:
        db.close()


if __name__ == "__main__":
    print("Starting development data seeding...", flush=True)
    seed_development_data()
    print("Seeding completed successfully!", flush=True)
