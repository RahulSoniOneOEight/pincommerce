"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const sections: { heading: string; items: { href: string; label: string }[] }[] = [
  {
    heading: "Commerce",
    items: [
      { href: "/", label: "Dashboard" },
      { href: "/products", label: "Products" },
      { href: "/orders", label: "Orders" },
    ],
  },
  {
    heading: "ERP",
    items: [
      { href: "/sales-orders", label: "Sales orders" },
      { href: "/inventory", label: "Inventory" },
    ],
  },
  {
    heading: "Operations",
    items: [{ href: "/exceptions", label: "Exceptions" }],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <nav className="admin-nav" aria-label="Admin">
      <div className="admin-brand">PinCommerce</div>
      {sections.map((section) => (
        <div className="admin-nav-group" key={section.heading}>
          <div className="admin-nav-heading">{section.heading}</div>
          {section.items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={pathname === item.href ? "page" : undefined}
              className="admin-nav-item"
            >
              {item.label}
            </Link>
          ))}
        </div>
      ))}
    </nav>
  );
}
