import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "IPC-BNS Cross-Reference Guide" };

const mappings = [
  { ipc: "302", bns: "101", offence: "Murder" },
  { ipc: "304", bns: "103(1)", offence: "Culpable homicide not amounting to murder" },
  { ipc: "307", bns: "109", offence: "Attempt to murder" },
  { ipc: "376", bns: "63", offence: "Rape" },
  { ipc: "379", bns: "303", offence: "Theft" },
  { ipc: "380", bns: "305", offence: "Theft in dwelling house" },
  { ipc: "384", bns: "308", offence: "Extortion" },
  { ipc: "392", bns: "309", offence: "Robbery" },
  { ipc: "406", bns: "316", offence: "Criminal breach of trust" },
  { ipc: "415", bns: "318", offence: "Cheating" },
  { ipc: "420", bns: "318", offence: "Cheating and dishonestly inducing delivery of property" },
  { ipc: "498A", bns: "85", offence: "Cruelty by husband or relatives" },
  { ipc: "120B", bns: "61", offence: "Criminal conspiracy" },
  { ipc: "144", bns: "141", offence: "Unlawful assembly" },
  { ipc: "147", bns: "142", offence: "Rioting" },
  { ipc: "299", bns: "100", offence: "Culpable homicide" },
  { ipc: "300", bns: "101", offence: "Murder (definition)" },
  { ipc: "303", bns: "100", offence: "Culpable homicide by causing death" },
  { ipc: "306", bns: "108", offence: "Abetment of suicide" },
  { ipc: "354", bns: "74", offence: "Assault on woman with intent to outrage modesty" },
  { ipc: "493", bns: "82", offence: "Cohabitation caused by deceitfully induced belief" },
  { ipc: "494", bns: "82", offence: "Marrying again during lifetime of husband or wife" },
  { ipc: "495", bns: "82", offence: "Same offence with concealment of former marriage" },
  { ipc: "498", bns: "85", offence: "Enticing or taking away married woman" },
];

export default function Page() {
  return (
    <SubPageLayout title="IPC to BNS Cross-Reference Guide" description="Complete mapping of Indian Penal Code sections to their Bharatiya Nyaya Sanhita equivalents. HECTOR maintains 496 cross-reference entries.">
      <div className="mb-6">
        <p className="text-sm text-silver">
          The Bharatiya Nyaya Sanhita (BNS) 2023 replaced the Indian Penal Code (IPC) 1860.
          Below are the most commonly referenced cross-references. HECTOR indexes all 496 mappings.
        </p>
      </div>
      <div className="bg-slate-custom rounded-xl border border-white/5 overflow-hidden">
        <div className="grid grid-cols-3 gap-px bg-white/5 text-xs font-medium text-silver uppercase tracking-wider">
          <div className="bg-slate-custom px-4 py-3">IPC Section</div>
          <div className="bg-slate-custom px-4 py-3">BNS Section</div>
          <div className="bg-slate-custom px-4 py-3">Offence</div>
        </div>
        <div className="divide-y divide-white/5">
          {mappings.map((m) => (
            <div key={m.ipc + m.bns} className="grid grid-cols-3 gap-px">
              <div className="bg-slate-custom px-4 py-3 text-sm text-gold font-mono">Section {m.ipc} IPC</div>
              <div className="bg-slate-custom px-4 py-3 text-sm text-gold font-mono">Section {m.bns} BNS</div>
              <div className="bg-slate-custom px-4 py-3 text-sm text-silver">{m.offence}</div>
            </div>
          ))}
        </div>
      </div>
      <p className="text-xs text-silver mt-4">
        Showing 24 of 496 cross-reference entries. Full mapping available via the API.
      </p>
    </SubPageLayout>
  );
}
