#!/usr/bin/env python3
"""Self-contained mock of the Medusa v2 storefront REST API.

Serves the endpoints used by the PinCommerce Flutter storefront (products and
carts) against a seeded INR catalog, so the app can be exercised end-to-end
without standing up a real Medusa backend.

This mirrors the repo's "mock in staging, real in prod" policy. The production
path is a real Medusa instance (see README.md).

Usage:
    python server.py [--host 127.0.0.1] [--port 9000]
"""
from __future__ import annotations

import argparse
import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


def _product(pid: str, title: str, description: str, amount: int) -> dict:
    """Build a product with a single default variant (amount in paise)."""
    return {
        "id": pid,
        "title": title,
        "description": description,
        "thumbnail": None,
        "variants": [
            {
                "id": f"variant_{pid}",
                "title": "Default",
                "prices": [{"amount": amount, "currency_code": "inr"}],
                "calculated_price": {"calculated_amount": amount},
            }
        ],
    }


PRODUCTS: list[dict] = [
    _product("prod_001", "Wireless Headphones", "Over-ear noise-cancelling headphones.", 199900),
    _product("prod_002", "Leather Sneakers", "Everyday leather sneakers.", 349900),
    _product("prod_003", "Cotton T-Shirt", "100% cotton crew-neck t-shirt.", 49900),
    _product("prod_004", "Smart Watch", "Fitness and notifications smart watch.", 249900),
    _product("prod_005", "Travel Backpack", "22L water-resistant backpack.", 129900),
    _product("prod_006", "Desk Lamp", "Adjustable LED desk lamp.", 89900),
]

VARIANT_INDEX: dict[str, tuple[dict, dict]] = {
    variant["id"]: (product, variant)
    for product in PRODUCTS
    for variant in product["variants"]
}

CARTS: dict[str, dict] = {}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length)) or {}
        except json.JSONDecodeError:
            return {}

    def log_message(self, *args) -> None:  # silence default request logging
        pass

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-publishable-api-key")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/health":
            return self._send(200, {"status": "ok"})
        if path == "/store/products":
            return self._list_products(parsed)
        if path.startswith("/store/products/"):
            return self._get_product(path.rsplit("/", 1)[1])
        if path.startswith("/store/carts/"):
            return self._get_cart(path.split("/")[3])
        self._send(404, {"message": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()
        if path == "/store/carts":
            return self._create_cart()
        if "/line-items/" in path:
            parts = path.split("/")  # ['', 'store', 'carts', id, 'line-items', line_id]
            if parts[4] == "line-items" and len(parts) == 6:
                return self._update_line_item(parts[3], parts[5], body)
        if path.endswith("/line-items"):
            parts = path.split("/")  # ['', 'store', 'carts', id, 'line-items']
            return self._add_line_item(parts[3], body)
        if path.endswith("/complete"):
            return self._complete(path.split("/")[3])
        if path.startswith("/store/carts/"):
            return self._update_cart(path.split("/")[3], body)
        self._send(404, {"message": "not found"})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if "/line-items/" in path:
            parts = path.split("/")
            return self._remove_line_item(parts[3], parts[5])
        self._send(404, {"message": "not found"})

    # --- products -----------------------------------------------------------

    def _list_products(self, parsed) -> None:
        qs = parse_qs(parsed.query)
        offset = int(qs.get("offset", ["0"])[0])
        limit = int(qs.get("limit", ["20"])[0])
        self._send(200, {
            "products": PRODUCTS[offset:offset + limit],
            "count": len(PRODUCTS),
            "limit": limit,
            "offset": offset,
        })

    def _get_product(self, pid: str) -> None:
        for product in PRODUCTS:
            if product["id"] == pid:
                return self._send(200, {"product": product})
        self._send(404, {"message": "product not found"})

    # --- carts --------------------------------------------------------------

    def _new_cart(self) -> dict:
        cart = {
            "id": f"cart_{uuid.uuid4().hex[:16]}",
            "items": [],
            "total": 0,
            "currency_code": "inr",
            "email": None,
            "shipping_address": None,
        }
        CARTS[cart["id"]] = cart
        return cart

    def _recompute(self, cart: dict) -> None:
        cart["total"] = sum(item["total"] for item in cart["items"])

    def _create_cart(self) -> None:
        self._send(200, {"cart": self._new_cart()})

    def _get_cart(self, cart_id: str) -> None:
        cart = CARTS.get(cart_id)
        if cart is None:
            return self._send(404, {"message": "cart not found"})
        self._send(200, {"cart": cart})

    def _add_line_item(self, cart_id: str, body: dict) -> None:
        cart = CARTS.get(cart_id)
        if cart is None:
            return self._send(404, {"message": "cart not found"})
        entry = VARIANT_INDEX.get(body.get("variant_id"))
        if entry is None:
            return self._send(404, {"message": "variant not found"})
        product, variant = entry
        quantity = int(body.get("quantity", 1))
        amount = variant["calculated_price"]["calculated_amount"]
        cart["items"].append({
            "id": f"cali_{uuid.uuid4().hex[:12]}",
            "title": product["title"],
            "quantity": quantity,
            "unit_price": amount,
            "total": amount * quantity,
            "variant_id": variant["id"],
        })
        self._recompute(cart)
        self._send(200, {"cart": cart})

    def _update_line_item(self, cart_id: str, line_id: str, body: dict) -> None:
        cart = CARTS.get(cart_id)
        if cart is None:
            return self._send(404, {"message": "cart not found"})
        quantity = int(body.get("quantity", 1))
        for item in cart["items"]:
            if item["id"] == line_id:
                item["quantity"] = quantity
                item["total"] = item["unit_price"] * quantity
        self._recompute(cart)
        self._send(200, {"cart": cart})

    def _remove_line_item(self, cart_id: str, line_id: str) -> None:
        cart = CARTS.get(cart_id)
        if cart is None:
            return self._send(404, {"message": "cart not found"})
        cart["items"] = [i for i in cart["items"] if i["id"] != line_id]
        self._recompute(cart)
        self._send(200, {"cart": cart})

    def _update_cart(self, cart_id: str, body: dict) -> None:
        cart = CARTS.get(cart_id)
        if cart is None:
            return self._send(404, {"message": "cart not found"})
        if "email" in body:
            cart["email"] = body["email"]
        if "shipping_address" in body:
            cart["shipping_address"] = body["shipping_address"]
        self._send(200, {"cart": cart})

    def _complete(self, cart_id: str) -> None:
        cart = CARTS.get(cart_id)
        if cart is None:
            return self._send(404, {"message": "cart not found"})
        order = {
            "id": f"order_{uuid.uuid4().hex[:16]}",
            "items": cart["items"],
            "total": cart["total"],
            "currency_code": cart["currency_code"],
            "status": "pending",
        }
        self._send(200, {"type": "order", "order": order})


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock Medusa v2 storefront server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Mock Medusa storefront listening on http://{args.host}:{args.port}")
    print(f"Seeded products: {len(PRODUCTS)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
