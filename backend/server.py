from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List

ROOT_DIR = Path(__file__).parent
FRONTEND_DIR = ROOT_DIR.parent / "frontend" / "public"

# MongoDB
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

# JWT
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 48

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────── Models ───────────────

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    token: str

class ProductIn(BaseModel):
    en: str
    el: str = ""
    price: str = ""
    cat: str = "cakes"
    den: str = ""
    # 'del' is a Python keyword — use alias
    del_field: str = Field(default="", alias="del")
    lf: bool = False
    pop: bool = False
    img: Optional[str] = None
    g: str = "g2"
    model_config = {"populate_by_name": True}

class ProductPatch(BaseModel):
    en: Optional[str] = None
    el: Optional[str] = None
    price: Optional[str] = None
    cat: Optional[str] = None
    den: Optional[str] = None
    del_field: Optional[str] = Field(default=None, alias="del")
    lf: Optional[bool] = None
    pop: Optional[bool] = None
    img: Optional[str] = None
    g: Optional[str] = None
    model_config = {"populate_by_name": True}

# ─────────────── Auth helpers ───────────────

def create_admin_token() -> str:
    payload = {
        "sub": "admin",
        "admin": True,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def require_admin(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if not payload.get("admin"):
            raise HTTPException(status_code=403, detail="Not authorized")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired — please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ─────────────── Default products for seeding ───────────────

DEFAULT_PRODUCTS = [
    # CAKES
    {"cat": "cakes", "g": "g5", "en": "Geography Cake 150g", "el": "Κέικ Γεωγραφίας 150g", "price": "2.75", "lf": True, "den": "Gluten-free & lactose-free sponge cake.", "del": "Παντεσπάνι χωρίς γλουτένη & λακτόζη."},
    {"cat": "cakes", "g": "g2", "en": "Orange Cake 150g", "el": "Κέικ Πορτοκάλι 150g", "price": "2.75", "lf": True, "den": "Zesty orange sponge — gluten-free & lactose-free.", "del": "Αρωματικό πορτοκάλι — χωρίς γλουτένη & λακτόζη."},
    {"cat": "cakes", "g": "g1", "en": "Chocolate Cake 150g", "el": "Σοκολατένιο Κέικ 150g", "price": "2.75", "lf": True, "den": "Rich chocolate sponge — gluten-free & lactose-free.", "del": "Πλούσιο σοκολατένιο — χωρίς γλουτένη & λακτόζη."},
    # DESSERTS
    {"cat": "desserts", "g": "g3", "en": "Cheesecake", "el": "Cheesecake", "price": "5.40", "lf": False, "den": "Buttered digestive biscuit base with lemon cream cheese & blackcurrant.", "del": "Βάση μπισκότου με κρέμα τυριού λεμόνι & μαύρο φραγκοστάφυλο."},
    {"cat": "desserts", "g": "g6", "en": "Apple Pie 180g", "el": "Μηλόπιτα 180g", "price": "5.40", "lf": True, "den": "Apple pieces with cinnamon in biscuit dough. Lactose-free.", "del": "Κομμάτια μήλου με κανέλα σε ζύμη μπισκότου. Χωρίς λακτόζη."},
    {"cat": "desserts", "g": "g3", "en": "Profiterole Dubai 180g", "el": "Προφιτερόλ Dubai 180g", "price": "6.00", "lf": False, "den": "Crackling pistachio, namelaka & praline pistachio.", "del": "Τραγανό φιστίκι, namelaka & πραλίνα φιστικιού."},
    {"cat": "desserts", "g": "g2", "en": "Strawberry Panna Cotta 180g", "el": "Panna Cotta Φράουλα 180g", "price": "4.80", "lf": False, "den": "Strawberry sauce with strawberry bits & panna cotta cream.", "del": "Σάλτσα φράουλας με κομμάτια φράουλας & κρέμα panna cotta."},
    {"cat": "desserts", "g": "g5", "en": "Duchess Milk Chocolate 180g", "el": "Δουκίσσα Σοκολάτα Γάλακτος 180g", "price": "5.40", "lf": False, "den": "Classic duchess with milk. Fluffier & more chocolatey than ever.", "del": "Κλασική δουκίσσα με γάλα. Πιο αφράτη & σοκολατένια από ποτέ."},
    {"cat": "desserts", "g": "g1", "en": "Chocolate Ganache 180g", "el": "Chocolate Ganache 180g", "price": "6.00", "lf": False, "den": "Chocolate ganache with chocolate sponge cake.", "del": "Ganache σοκολάτας με σοκολατένιο παντεσπάνι."},
    {"cat": "desserts", "g": "g2", "en": "Carrot Cake", "el": "Carrot Cake", "price": "5.40", "lf": False, "den": "Carrot sponge cake flavoured with cinnamon & buttercream.", "del": "Παντεσπάνι καρότου με κανέλα & βουτυρόκρεμα."},
    {"cat": "desserts", "g": "g1", "en": "Brownie Cheese 90g", "el": "Brownie Cheese 90g", "price": "3.20", "lf": False, "den": "Rich chocolate & creamy cheese in a dessert that melts in the mouth.", "del": "Πλούσια σοκολάτα & κρεμώδες τυρί που λιώνει στο στόμα."},
    {"cat": "desserts", "g": "g6", "en": "Butter Almond Kourabiedes", "el": "Κουραμπιέδες Αμυγδάλου", "price": "3.00", "lf": False, "den": "Buttery almond kourabiedes.", "del": "Βουτυρένιοι κουραμπιέδες αμυγδάλου."},
    # COOKIES
    {"cat": "cookies", "g": "g6", "en": "Cinnamon Cookies 200g", "el": "Μπισκότα Κανέλας 200g", "price": "5.00", "lf": True, "den": "Handmade traditional. Lactose-free.", "del": "Χειροποίητα παραδοσιακά. Χωρίς λακτόζη."},
    {"cat": "cookies", "g": "g6", "en": "Orange Cookies 200g", "el": "Μπισκότα Πορτοκάλι 200g", "price": "5.00", "lf": True, "den": "Handmade traditional. Lactose-free.", "del": "Χειροποίητα παραδοσιακά. Χωρίς λακτόζη."},
    # SAVOURY
    {"cat": "savory", "g": "g4", "en": "Sausage Pie Kourou w/ Philadelphia 140g", "el": "Πίτα Λουκάνικο Κουρού 140g", "price": "4.00", "lf": False, "den": "Frankfurt sausage & cream cheese in phyllo dough.", "del": "Λουκάνικο Φρανκφούρτης & κρέμα τυριού σε φύλλο."},
    {"cat": "savory", "g": "g4", "en": "Kourou Cheese Pie 140g", "el": "Τυρόπιτα Κουρού 140g", "price": "4.00", "lf": False, "den": "Feta in kourou pastry.", "del": "Φέτα σε ζύμη κουρού."},
    {"cat": "savory", "g": "g6", "en": "Tahini Pie 270g", "el": "Ταχινόπιτα 270g", "price": "5.40", "lf": True, "den": "Traditional handmade. Gluten-free & lactose-free. Vegetarian.", "del": "Παραδοσιακή χειροποίητη. Χωρίς γλουτένη & λακτόζη."},
    {"cat": "savory", "g": "g4", "en": "Cheese, Bacon & Tomato Peinirli", "el": "Πεϊνιρλί Τυρί-Μπέικον-Ντομάτα", "price": "7.20", "lf": False, "den": "Gluten-free peinirli with cheese, bacon & tomato.", "del": "Πεϊνιρλί χωρίς γλουτένη με τυρί, μπέικον & ντομάτα."},
    {"cat": "savory", "g": "g4", "en": "Rustic Olive Pie 300g", "el": "Χωριάτικη Ελιόπιτα 300g", "price": "5.40", "lf": True, "den": "Gluten-free. Vegan. With Thassos black olives.", "del": "Χωρίς γλουτένη. Vegan. Με ελιές Θάσου."},
    # BAKERY
    {"cat": "bakery", "g": "g4", "en": "Focaccia 179g", "el": "Focaccia 179g", "price": "4.80", "lf": True, "den": "Gluten-free & lactose-free. Suitable for vegetarians.", "del": "Χωρίς γλουτένη & λακτόζη. Κατάλληλο για χορτοφάγους."},
    {"cat": "bakery", "g": "g4", "en": "Thessaloniki Bagel 100g", "el": "Κουλούρι Θεσσαλονίκης 100g", "price": "1.80", "lf": True, "den": "Traditional gluten-free Thessaloniki bagel.", "del": "Παραδοσιακό κουλούρι Θεσσαλονίκης χωρίς γλουτένη."},
    {"cat": "bakery", "g": "g4", "en": "Oven-Baked Pasta 400g", "el": "Παστίτσιο Φούρνου 400g", "price": "7.20", "lf": False, "den": "Gluten-free penne with pork mince & tomato.", "del": "Πέννες χωρίς γλουτένη με κιμά χοιρινό & ντομάτα."},
    # FROZEN
    {"cat": "frozen", "g": "g4", "en": "Frozen Sausage Rolls, Cheese Pies & Pizzas 1kg", "el": "Κατεψυγμένα Μείγμα 1kg", "price": "17.50", "lf": False, "den": "Mix of frozen sausage rolls, cheese pies & pizzas.", "del": "Μείγμα κατεψυγμένων ρολών, τυρόπιτων & πίτσας."},
    {"cat": "frozen", "g": "g6", "en": "Frozen Tahini Pie", "el": "Κατεψυγμένη Ταχινόπιτα", "price": "5.20", "lf": True, "den": "Gluten-free & lactose-free. Vegetarian.", "del": "Χωρίς γλουτένη & λακτόζη. Χορτοφαγικό."},
    {"cat": "frozen", "g": "g4", "en": "Frozen Cheese Pie 170g", "el": "Κατεψυγμένη Τυρόπιτα 170g", "price": "3.80", "lf": False, "den": "Gluten-free cheese pie.", "del": "Τυρόπιτα χωρίς γλουτένη."},
    {"cat": "frozen", "g": "g4", "en": "Frozen Olive Pie 300g", "el": "Κατεψυγμένη Ελιόπιτα 300g", "price": "5.20", "lf": True, "den": "Gluten-free & lactose-free. Vegetarian.", "del": "Χωρίς γλουτένη & λακτόζη. Χορτοφαγικό."},
    {"cat": "frozen", "g": "g4", "en": "Frozen Thessaloniki Bagels 200g", "el": "Κατεψυγμένα Κουλούρια 200g", "price": "3.35", "lf": True, "den": "Gluten-free & lactose-free. Vegetarian.", "del": "Χωρίς γλουτένη & λακτόζη. Χορτοφαγικό."},
    {"cat": "frozen", "g": "g4", "en": "Buckwheat Loaf, Frozen 170g", "el": "Ψωμί Φαγόπυρου 170g", "price": "2.40", "lf": True, "den": "Gluten-free & lactose-free. Vegetarian.", "del": "Χωρίς γλουτένη & λακτόζη. Χορτοφαγικό."},
    {"cat": "frozen", "g": "g4", "en": "Frozen Oven Pasta 450g", "el": "Κατεψυγμένο Παστίτσιο 450g", "price": "7.20", "lf": False, "den": "Gluten-free oven-baked pasta.", "del": "Παστίτσιο φούρνου χωρίς γλουτένη."},
    # POPULAR / CUSTOM
    {"cat": "savory", "g": "g4", "en": "Make Your Own GF Sandwich", "el": "Φτιάξε το Σάντουιτς σου", "price": "from 4.00", "lf": False, "pop": True, "den": "Build your own gluten-free sandwich with your favourite ingredients. 1st most ordered.", "del": "Φτιάξε το δικό σου σάντουιτς χωρίς γλουτένη. Το πιο δημοφιλές."},
    {"cat": "custom", "g": "g2", "en": "Custom Celebration Cakes", "el": "Τούρτες Εκδηλώσεων", "price": "on request", "lf": False, "den": "Birthdays, christenings, weddings — made to order. Call Evridiki directly.", "del": "Γενέθλια, βαφτίσεις, γάμοι — κατά παραγγελία. Κάλεσε την Ευρυδίκη."},
]

# ─────────────── Startup ───────────────

@app.on_event("startup")
async def startup():
    await db.products.create_index("id", unique=True)
    count = await db.products.count_documents({})
    if count == 0:
        docs = [{"id": f"seed{i}", "order": i, **p} for i, p in enumerate(DEFAULT_PRODUCTS)]
        await db.products.insert_many(docs)
        logger.info(f"Seeded {len(docs)} default products")

@app.on_event("shutdown")
async def shutdown():
    client.close()

# ─────────────── Routes ───────────────

@api_router.get("/health")
async def health():
    return {"status": "ok"}

@api_router.post("/admin/login", response_model=LoginResponse)
async def admin_login(req: LoginRequest):
    admin_pw = os.environ.get("ADMIN_PASSWORD", "evridiki2025")
    if req.password != admin_pw:
        raise HTTPException(status_code=401, detail="Wrong password")
    return LoginResponse(token=create_admin_token())

@api_router.get("/products")
async def list_products():
    docs = await db.products.find({}, {"_id": 0}).sort("order", 1).to_list(2000)
    return docs

@api_router.post("/products", dependencies=[Depends(require_admin)])
async def create_product(product: ProductIn):
    count = await db.products.count_documents({})
    data = product.model_dump(by_alias=True)
    # rename 'del' key stored by alias
    doc = {
        "id": "p" + uuid.uuid4().hex[:8],
        "order": count,
        **data,
    }
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.put("/products/{pid}", dependencies=[Depends(require_admin)])
async def update_product(pid: str, product: ProductPatch):
    # Only set fields that were explicitly provided (not None)
    update = {k: v for k, v in product.model_dump(by_alias=True).items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Nothing to update")
    result = await db.products.update_one({"id": pid}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    doc = await db.products.find_one({"id": pid}, {"_id": 0})
    return doc

@api_router.delete("/products/{pid}", dependencies=[Depends(require_admin)])
async def delete_product(pid: str):
    result = await db.products.delete_one({"id": pid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"deleted": pid}

@api_router.patch("/products/{pid}/toggle-pop", dependencies=[Depends(require_admin)])
async def toggle_pop(pid: str):
    doc = await db.products.find_one({"id": pid}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    new_pop = not doc.get("pop", False)
    await db.products.update_one({"id": pid}, {"$set": {"pop": new_pop}})
    return {"id": pid, "pop": new_pop}

app.include_router(api_router)

# ─────────────── Serve frontend static files ───────────────
# Mount images folder, then fall back to index.html for all other routes
if FRONTEND_DIR.exists():
    images_dir = FRONTEND_DIR / "images"
    if images_dir.exists():
        app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        return FileResponse(str(FRONTEND_DIR / "index.html"))
