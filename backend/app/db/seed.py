from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Firm, LegalSource, Matter, Membership, User
from app.db.session import SessionLocal


def seed_development_data() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(Firm).where(Firm.id == "firm_vakil_demo")):
            return

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
        db.add_all(
            [
                LegalSource(
                    id="src_constitution",
                    title="Constitution of India",
                    source_type="act",
                    jurisdiction="India",
                    year=1950,
                    public_url="https://www.indiacode.nic.in/",
                ),
                LegalSource(
                    id="src_bns_2023",
                    title="Bharatiya Nyaya Sanhita, 2023",
                    source_type="act",
                    jurisdiction="India",
                    year=2023,
                    public_url="https://www.indiacode.nic.in/",
                ),
                LegalSource(
                    id="src_bnss_2023",
                    title="Bharatiya Nagarik Suraksha Sanhita, 2023",
                    source_type="act",
                    jurisdiction="India",
                    year=2023,
                    public_url="https://www.indiacode.nic.in/",
                ),
                LegalSource(
                    id="src_limitation_1963",
                    title="Limitation Act, 1963",
                    source_type="act",
                    jurisdiction="India",
                    year=1963,
                    public_url="https://www.indiacode.nic.in/",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()
