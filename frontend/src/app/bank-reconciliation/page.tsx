"use client";

import { useState } from "react";
import { useClient } from "@/contexts/ClientContext";
import { toast } from "@/lib/toast";

interface BankTransaction {
  date: string;
  amount: number;
  description: string;
  reference: string;
}

interface GLEntry {
  entry_id: string;
  date: string;
  amount: number;
  voucher_number: string;
  description: string;
}

interface MatchResult {
  bank: BankTransaction;
  gl?: GLEntry;
  confidence?: number;
  method?: string;
  reasoning?: string;
  possible_matches?: any[];
  status?: string;
  reason?: string;
}

export default function BankReconciliationPage() {
  const { selectedClient } = useClient();
  const [uploading, setUploading] = useState(false);
  const [bankAccount, setBankAccount] = useState("1920");
  const [results, setResults] = useState<any>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedClient) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `http://localhost:8000/api/bank/reconciliation/upload?client_id=${selectedClient.id}&bank_account=${bankAccount}`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Upload error:", error);
      toast.error("Feil ved opplasting. Se konsoll for detaljer.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-darkest text-text-primary px-8 py-7">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-text-primary mb-2">
          Bankavstemming
        </h1>
        <p className="text-text-secondary">
          Last opp bankutskrift for automatisk matching med hovedbok
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-bg-dark rounded-lg p-6 mb-6 border border-border-light">
        <h2 className="text-xl font-semibold mb-4">Last opp bankutskrift</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Bankkonto (hovedbokskonto)
            </label>
            <input
              type="text"
              value={bankAccount}
              onChange={(e) => setBankAccount(e.target.value)}
              className="w-full px-3 py-2 bg-bg-darker border border-border-light rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary"
              placeholder="f.eks. 1920"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Velg fil (CSV)
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              disabled={uploading || !selectedClient}
              className="w-full px-3 py-2 bg-bg-darker border border-border-light rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-primary file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-accent-primary file:text-white hover:file:bg-accent-secondary"
            />
          </div>
        </div>

        {uploading && (
          <div className="text-accent-primary">Laster opp og matcher...</div>
        )}

        {!selectedClient && (
          <div className="text-yellow-500 text-sm mt-2">
            Velg en klient først (øverst til høyre)
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-bg-dark rounded-lg p-6 border border-border-light">
            <h2 className="text-xl font-semibold mb-4">Sammendrag</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-text-secondary text-sm">
                  Banktransaksjoner
                </div>
                <div className="text-3xl font-bold">
                  {results.summary.total_bank_transactions}
                </div>
              </div>
              <div>
                <div className="text-text-secondary text-sm">
                  Auto-matchet
                </div>
                <div className="text-3xl font-bold text-green-500">
                  {results.summary.auto_matched}
                </div>
              </div>
              <div>
                <div className="text-text-secondary text-sm">
                  AI-assistert
                </div>
                <div className="text-3xl font-bold text-blue-500">
                  {results.summary.ai_assisted}
                </div>
              </div>
              <div>
                <div className="text-text-secondary text-sm">
                  Trenger gjennomgang
                </div>
                <div className="text-3xl font-bold text-yellow-500">
                  {results.summary.needs_review}
                </div>
              </div>
            </div>

            <div className="mt-4">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Match-rate:</span>
                <span className="text-2xl font-bold text-accent-primary">
                  {results.summary.match_rate}%
                </span>
              </div>
              <div className="mt-2 h-2 bg-bg-darker rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent-primary"
                  style={{ width: `${results.summary.match_rate}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Auto-matched */}
          {results.auto_matched.length > 0 && (
            <div className="bg-bg-dark rounded-lg p-6 border border-green-500">
              <h2 className="text-xl font-semibold mb-4 text-green-500">
                ✅ Auto-matchet ({results.auto_matched.length})
              </h2>
              <div className="space-y-4">
                {results.auto_matched.map((match: MatchResult, idx: number) => (
                  <div
                    key={idx}
                    className="bg-bg-darker p-4 rounded-lg border border-border-light"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-text-secondary mb-1">
                          BANK
                        </div>
                        <div className="font-semibold">{match.bank.date}</div>
                        <div className="text-sm">{match.bank.description}</div>
                        <div className="text-lg font-bold mt-1">
                          {match.bank.amount.toLocaleString("nb-NO")} kr
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-text-secondary mb-1">
                          HOVEDBOK
                        </div>
                        <div className="font-semibold">
                          {match.gl?.date} - {match.gl?.voucher_number}
                        </div>
                        <div className="text-sm">{match.gl?.description}</div>
                        <div className="text-lg font-bold mt-1">
                          {match.gl?.amount.toLocaleString("nb-NO")} kr
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-green-500">
                      Confidence: {match.confidence}% ({match.method})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Needs Review */}
          {results.needs_review.length > 0 && (
            <div className="bg-bg-dark rounded-lg p-6 border border-yellow-500">
              <h2 className="text-xl font-semibold mb-4 text-yellow-500">
                ⚠️ Trenger gjennomgang ({results.needs_review.length})
              </h2>
              <div className="space-y-4">
                {results.needs_review.map((item: MatchResult, idx: number) => (
                  <div
                    key={idx}
                    className="bg-bg-darker p-4 rounded-lg border border-border-light"
                  >
                    <div className="mb-2">
                      <div className="text-xs text-text-secondary mb-1">
                        BANK
                      </div>
                      <div className="font-semibold">{item.bank.date}</div>
                      <div className="text-sm">{item.bank.description}</div>
                      <div className="text-lg font-bold mt-1">
                        {item.bank.amount.toLocaleString("nb-NO")} kr
                      </div>
                    </div>

                    {item.possible_matches && item.possible_matches.length > 0 ? (
                      <div className="mt-4">
                        <div className="text-sm text-text-secondary mb-2">
                          Mulige matcher:
                        </div>
                        {item.possible_matches.map((pm: any, pmIdx: number) => (
                          <div
                            key={pmIdx}
                            className="bg-bg-darkest p-3 rounded mb-2 border border-border-light"
                          >
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="text-sm">{pm.gl.description}</div>
                                <div className="text-xs text-text-secondary">
                                  {pm.gl.date} - {pm.gl.voucher_number}
                                </div>
                              </div>
                              <button className="px-3 py-1 bg-accent-primary text-white rounded text-sm hover:bg-accent-secondary">
                                Match
                              </button>
                            </div>
                            <div className="text-xs text-text-secondary mt-1">
                              Score: {pm.similarity_score}% -{" "}
                              {pm.reasons.join(", ")}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="mt-2 text-sm text-text-secondary">
                        Ingen forslag funnet. Opprett bilag manuelt?
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
