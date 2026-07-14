import { notFound } from "next/navigation";
import { getDemoBySlug } from "@/lib/db";
import AiOpsChatSandbox from "@/components/AiOpsChatSandbox";

export const dynamic = "force-dynamic"; // always read the latest DB row, no static caching

export default async function DemoPage({
  params,
}: {
  params: { slug: string };
}) {
  const demo = await getDemoBySlug(params.slug);
  if (!demo) notFound();

  const { business_name, category, city, owner_first_name, chat_script } = demo.content;

  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-10 md:py-16">
      <div className="w-full max-w-2xl space-y-8">
        <header className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-xs font-mono border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Built for {business_name}
          </div>
          <h1 className="text-3xl font-extrabold text-white">
            Hi {owner_first_name || "there"} — this is what your AI Operations
            Manager looks like for {business_name}.
          </h1>
          <p className="text-sm text-slate-400 max-w-lg mx-auto">
            Every missed call and after-hours text from a {category.toLowerCase()}{" "}
            customer in {city} gets answered instantly, qualified, and booked —
            without anyone lifting a finger. Try it below.
          </p>
        </header>

        <AiOpsChatSandbox businessName={business_name} script={chat_script} />

        <footer className="text-center text-xs text-slate-500 space-y-1">
          <p>This demo was built for {business_name} by Exclusive Media's AI Operations Manager.</p>
          <p>Reply to the email you received to get this live on your own number.</p>
        </footer>
      </div>
    </main>
  );
}
