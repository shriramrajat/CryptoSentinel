const adapters = [
  ['Binary discovery', 'ELF and PE indicators, libraries, and imported symbols'],
  ['Container discovery', 'OCI/Docker archives and filesystem manifests without execution'],
  ['Dependency intelligence', 'Manifest presence is kept separate from observed usage'],
  ['Protocol intelligence', 'TLS, SSH, JWT, JWS, and JWE configuration evidence'],
  ['Bounded query', 'Allowlisted inventory questions with deterministic results'],
  ['Copilot boundary', 'Evidence explanations only; deterministic engines remain authoritative'],
];

export default function AdvancedDiscoveryPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <p className="text-xs uppercase tracking-widest text-[#00E5FF]">Phase 5</p>
      <h1 className="text-3xl font-semibold text-[#F5F7FA] mt-2">Advanced Discovery</h1>
      <p className="text-[#A3ADBF] mt-3 max-w-3xl">Discover cryptographic indicators across artifacts, preserve evidence, and connect results to the existing enterprise inventory.</p>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 mt-8">
        {adapters.map(([title, description]) => (
          <section key={title} className="rounded-xl border border-[#232B3D] bg-[#0F1523]/70 p-5">
            <h2 className="text-lg font-medium text-[#F5F7FA]">{title}</h2>
            <p className="text-sm text-[#A3ADBF] mt-2">{description}</p>
          </section>
        ))}
      </div>
    </main>
  );
}
