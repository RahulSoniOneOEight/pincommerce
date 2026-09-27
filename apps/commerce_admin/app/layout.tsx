import type { ReactNode } from "react";
import "@pincommerce/agency-web-ui/styles.css";
import "./admin.css";
import { Sidebar } from "./sidebar";

export const metadata = { title: "PinCommerce Admin" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="admin-shell">
          <Sidebar />
          <main className="admin-main">{children}</main>
        </div>
      </body>
    </html>
  );
}
