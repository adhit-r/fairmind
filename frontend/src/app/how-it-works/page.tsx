export default function HowItWorksPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">How it works</h1>
      <p className="text-muted-foreground">High-level overview of calculations and pipeline.</p>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Authentication</h2>
        <ul className="list-disc pl-6 text-sm">
          <li>Supabase Auth (email/password) with `profiles` table and RLS.</li>
          <li>Frontend uses `@supabase/supabase-js` client with anon key.</li>
        </ul>
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Model upload</h2>
        <ul className="list-disc pl-6 text-sm">
          <li>POST `/models/upload` accepts `.pkl/.joblib/.pt/.onnx/.h5`.</li>
          <li>Files are stored in `backend/uploads/` with a SHA-256 fingerprint.</li>
          <li>For pickle/joblib, backend attempts a safe load for basic validation.</li>
        </ul>
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Run simulation</h2>
        <ul className="list-disc pl-6 text-sm">
          <li>POST `/simulation/run` with the `path` returned by upload.</li>
          <li>Returns mocked scores now: fairness, robustness, compliance.</li>
          <li>Replace with real inference/bias checks to go beyond mock.</li>
        </ul>
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Metrics (current)</h2>
        <ul className="list-disc pl-6 text-sm">
          <li><b>Fairness</b>: placeholder number in [0.6, 0.95] for demo.</li>
          <li><b>Robustness</b>: placeholder number in [0.5, 0.95].</li>
          <li><b>Compliance</b>: placeholder number in [0.55, 0.95].</li>
        </ul>
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Next steps</h2>
        <ul className="list-disc pl-6 text-sm">
          <li>Wire real model inference and fairness metrics (e.g., demographic parity, equal opportunity).</li>
          <li>Add per-feature explainability (SHAP/LIME) from backend endpoints.</li>
          <li>Persist artifacts to Supabase Storage and register metadata in DB.</li>
        </ul>
      </section>
    </div>
  )
}


