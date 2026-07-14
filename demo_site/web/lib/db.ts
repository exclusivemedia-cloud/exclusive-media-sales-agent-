import { Pool } from "pg";

let pool: Pool | undefined;

function getPool(): Pool {
  if (!pool) {
    if (!process.env.DATABASE_URL) {
      throw new Error("DATABASE_URL is not set");
    }
    pool = new Pool({ connectionString: process.env.DATABASE_URL });
  }
  return pool;
}

export type ChatMessage = {
  sender: "customer" | "ai";
  text: string;
};

export type DemoContent = {
  business_name: string;
  category: string;
  city: string;
  owner_first_name: string;
  chat_script: ChatMessage[];
};

export type DemoSite = {
  slug: string;
  content: DemoContent;
};

export async function getDemoBySlug(slug: string): Promise<DemoSite | null> {
  const { rows } = await getPool().query(
    "select slug, content from demo_sites where slug = $1 limit 1",
    [slug]
  );
  if (rows.length === 0) return null;
  return { slug: rows[0].slug, content: rows[0].content as DemoContent };
}

export async function hasProcessedStripeEvent(eventId: string): Promise<boolean> {
  const { rows } = await getPool().query(
    "select 1 from payments where stripe_event_id = $1",
    [eventId]
  );
  return rows.length > 0;
}

export async function markPaymentPaid(
  sessionId: string,
  eventId: string
): Promise<{ leadId: string; companyName: string } | null> {
  const pool = getPool();
  const { rows } = await pool.query(
    `update payments set status = 'paid', stripe_event_id = $2, updated_at = now()
     where stripe_session_id = $1
     returning lead_id`,
    [sessionId, eventId]
  );
  if (rows.length === 0) return null;

  const leadId = rows[0].lead_id;
  const { rows: leadRows } = await pool.query(
    `update leads set pipeline_state = 'PAID', updated_at = now()
     where id = $1
     returning company_name`,
    [leadId]
  );
  return { leadId, companyName: leadRows[0]?.company_name ?? "unknown business" };
}

export { getPool };
