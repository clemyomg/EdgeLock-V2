"use client";
import React, { useState, useEffect } from "react";

// ✅ Your Railway URL
const BACKEND_URL = "https://edgelock-v2-production.up.railway.app"; 

export default function EdgeLockPro() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${BACKEND_URL}/live-edges`)
      .then(res => {
        if (!res.ok) throw new Error(`Server Error: ${res.status}`);
        return res.json();
      })
      .then(data => {
        if(Array.isArray(data)) setMatches(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Fetch Error:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // --- NEW: Helper to group games by date ---
  const groupedMatches = matches.reduce((acc: any, match) => {
    const date = new Date(match.date);
    // Create a label like "Today", "Tomorrow", or "Sat, Oct 12"
    let label = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    
    // Simple "Today" / "Tomorrow" logic
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) label = "Today";
    else if (date.toDateString() === tomorrow.toDateString()) label = "Tomorrow";

    if (!acc[label]) acc[label] = [];
    acc[label].push(match);
    return acc;
  }, {});

  if (loading) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-emerald-500">Loading Market Data...</div>;
  if (error) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-red-500">Connection Failed: {error}</div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-4 font-sans pb-24">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-emerald-400">EdgeLock Pro</h1>
        <div className="text-xs bg-zinc-800 px-2 py-1 rounded text-zinc-400">Live Models</div>
      </div>

      {matches.length === 0 ? (
        <div className="text-zinc-500 text-center mt-10">No upcoming high-value matches found.</div>
      ) : (
        <div className="grid gap-8">
          {/* Render Groups */}
          {Object.entries(groupedMatches).map(([dateLabel, games]: [string, any]) => (
            <div key={dateLabel}>
              <h2 className="text-emerald-500/80 font-bold uppercase text-xs tracking-widest mb-3 pl-1 sticky top-0 bg-zinc-950/90 py-2 backdrop-blur-sm z-10">
                {dateLabel}
              </h2>
              <div className="grid gap-4">
                {games.map((m: any) => (
                  <MatchCard key={m.id} data={m} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// --- MAIN CARD COMPONENT ---
function MatchCard({ data }: { data: any }) {
  const [activeTab, setActiveTab] = useState("1X2");

  // Format Time (e.g., "18:30")
  const time = new Date(data.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-lg relative">
      {/* Date Badge */}
      <div className="absolute top-4 right-4 text-[10px] bg-zinc-900 text-zinc-500 px-2 py-0.5 rounded border border-zinc-800">
        {time}
      </div>

      {/* Header */}
      <div className="bg-zinc-900/50 p-4 border-b border-zinc-800">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">{data.league}</div>
        <div className="text-lg font-bold pr-10">{data.match}</div>
        
        {/* Tabs */}
        <div className="flex gap-2 mt-3 overflow-x-auto pb-1 no-scrollbar">
          {["1X2", "DC", "GOALS"].map(tab => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`text-xs px-3 py-1 rounded-full border transition-all whitespace-nowrap ${activeTab === tab ? "bg-emerald-500 text-black border-emerald-500 font-bold" : "border-zinc-700 text-zinc-400 hover:border-zinc-500"}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === "1X2" && (
          <>
            <BettingRow label="Home" prob={data.probs["1"]} fair={data.fair_odds["1"]} market={data.market_odds["1"]} />
            <BettingRow label="Draw" prob={data.probs["X"]} fair={data.fair_odds["X"]} market={data.market_odds["X"]} />
            <BettingRow label="Away" prob={data.probs["2"]} fair={data.fair_odds["2"]} market={data.market_odds["2"]} />
          </>
        )}

        {activeTab === "DC" && (
          <>
            <BettingRow label="1X (Home/Draw)" prob={data.probs["1X"]} fair={data.fair_odds["1X"]} market={0} />
            <BettingRow label="X2 (Draw/Away)" prob={data.probs["X2"]} fair={data.fair_odds["X2"]} market={0} />
          </>
        )}

        {activeTab === "GOALS" && (
          <>
            <BettingRow label="Over 2.5" prob={data.probs["O2.5"]} fair={data.fair_odds["O2.5"]} market={data.market_odds["O2.5"]} />
            <BettingRow label="Under 2.5" prob={data.probs["U2.5"]} fair={data.fair_odds["U2.5"]} market={data.market_odds["U2.5"]} />
            <BettingRow label="Over 1.5" prob={data.probs["O1.5"]} fair={data.fair_odds["O1.5"]} market={0} />
            <BettingRow label="Under 1.5" prob={data.probs["U1.5"]} fair={data.fair_odds["U1.5"]} market={0} />
          </>
        )}
      </div>
    </div>
  );
}

// --- SUB-COMPONENT: SAFE BETTING ROW (PREVENTS CRASHES) ---
function BettingRow({ label, prob, fair, market }: { label: string, prob: number, fair: number, market: number }) {
  const [userOdds, setUserOdds] = useState(market || 0);

  // Auto-update if backend sends new live odds
  useEffect(() => {
    if (market > 0) setUserOdds(market);
  }, [market]);

  const edge = userOdds > 0 ? ((prob / 100) * userOdds) - 1 : 0;
  const kelly = edge > 0 
    ? (((userOdds - 1) * (prob/100) - (1 - (prob/100))) / (userOdds - 1)) * 0.25 * 1000 
    : 0;

  return (
    <div className="grid grid-cols-4 gap-2 items-center mb-3 text-sm">
      <div className="text-zinc-400 font-bold">{label}</div>
      
      <div className="text-center">
        <div className="text-white font-bold">{prob?.toFixed(1)}%</div>
        <div className="text-[10px] text-zinc-600">Fair: {fair?.toFixed(2)}</div>
      </div>

      <input 
        type="number" 
        step="0.01"
        className="bg-zinc-900 border border-zinc-700 text-center text-emerald-400 font-mono rounded py-1 outline-none focus:border-emerald-500 transition-colors"
        value={userOdds}
        onChange={(e) => setUserOdds(parseFloat(e.target.value))}
      />

      <div className={`text-center font-bold border rounded py-1 flex flex-col justify-center min-h-[40px] ${edge > 0 ? "bg-emerald-900/20 border-emerald-500/50 text-emerald-400" : "bg-zinc-900 border-zinc-800 text-zinc-600"}`}>
        <span>{edge > 0 ? "+" : ""}{(edge * 100).toFixed(1)}%</span>
        {edge > 0 && <span className="text-[9px] text-emerald-600">€{kelly.toFixed(0)}</span>}
      </div>
    </div>
  );
}