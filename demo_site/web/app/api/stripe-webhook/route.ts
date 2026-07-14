import Stripe from "stripe";
import { hasProcessedStripeEvent, markPaymentPaid } from "@/lib/db";
import { notifyTelegram } from "@/lib/telegram";

export const runtime = "nodejs"; // needs Node crypto for signature verification

function getStripe(): Stripe {
  if (!process.env.STRIPE_SECRET_KEY) {
    throw new Error("STRIPE_SECRET_KEY is not set");
  }
  return new Stripe(process.env.STRIPE_SECRET_KEY);
}

export async function POST(req: Request) {
  const signature = req.headers.get("stripe-signature");
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!signature || !webhookSecret) {
    return new Response("Missing signature or webhook secret", { status: 400 });
  }

  const rawBody = await req.text();
  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (err) {
    return new Response(`Signature verification failed: ${(err as Error).message}`, {
      status: 400,
    });
  }

  if (event.type !== "checkout.session.completed") {
    return new Response("ignored", { status: 200 });
  }

  // Idempotency: Stripe can redeliver the same event.
  if (await hasProcessedStripeEvent(event.id)) {
    return new Response("already processed", { status: 200 });
  }

  const session = event.data.object as Stripe.Checkout.Session;
  const result = await markPaymentPaid(session.id, event.id);

  if (result) {
    await notifyTelegram(
      `💰 ${result.companyName} just paid for AI Operations Manager ($${((session.amount_total ?? 0) / 100).toFixed(0)}/mo). Lead marked PAID.`
    );
  }

  return new Response("ok", { status: 200 });
}
