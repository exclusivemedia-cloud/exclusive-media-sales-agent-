export default function ThankYouPage() {
  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="text-center space-y-3 max-w-md">
        <span className="material-icons text-emerald-400 text-4xl">check_circle</span>
        <h1 className="text-2xl font-bold text-white">You're all set.</h1>
        <p className="text-sm text-slate-400">
          Your AI Operations Manager is being provisioned. You'll get a text to
          the number on file once it's live — usually within 48 hours.
        </p>
      </div>
    </main>
  );
}
