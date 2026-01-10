"use client";
import React, { useState, useEffect } from "react";

// Use your PC's IP here
const BACKEND_URL = "edgelock-v2-production.up.railway.app"; 

export default function EdgeLockPro() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BACKEND_URL}/live-edges`)
      .then(res => res.json())
      .then(data => {
        if(Array.isArray(data)) setMatches(data);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, []);

  if (loading) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-emerald-500">Loading Market Data...</div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-4 font-sans pb-24">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-emerald-400">EdgeLock Pro</h1>
        <div className="text-xs bg-zinc-800 px-2 py-1 rounded text-zinc-400">Live Models</div>
      </div>

      <div className="grid gap-6">
        {matches.map((m) => (
          <MatchCard key={m.id} data={m} />
        ))}
      </div>
    </div>
  );
}

// --- SUB-COMPONENT: HANDLES THE INTERACTIVE MATH ---
function MatchCard({ data }: { data: any }) {
  const [activeTab, setActiveTab] = useState("1X2"); // 1X2 | DC | GOALS
  
  // Helper to render a betting row
  const renderRow = (label: string, probKey: string, oddsKey: string) => {
    const prob = data.probs[probKey];      // True Model %
    const fair = data.fair_odds[probKey];  // Model Fair Odds
    const market = data.market_odds[oddsKey] || 0; // Bookie Odds

    // State for interactive input (defaults to market odds)
    const [userOdds, setUserOdds] = useState(market);

    // Calculate Live Edge
    const edge = userOdds > 0 ? ((prob / 100) * userOdds) - 1 : 0;
    const edgePercent = (edge * 100).toFixed(1);
    
    // Kelly Bet (Bankroll €1000, 25% Fraction)
    const kelly = edge > 0 
      ? (((userOdds - 1) * (prob/100) - (1 - (prob/100))) / (userOdds - 1)) * 0.25 * 1000 
      : 0;

    return (
      <div className="grid grid-cols-4 gap-2 items-center mb-3 text-sm">
        {/* Label */}
        <div className="text-zinc-400 font-bold">{label}</div>
        
        {/* Model Stats */}
        <div className="text-center">
          <div className="text-white font-bold">{prob}%</div>
          <div className="text-[10px] text-zinc-600">Fair: {fair}</div>
        </div>

        {/* Interactive Input */}
        <input 
          type="number" 
          step="0.01"
          className="bg-zinc-900 border border-zinc-700 text-center text-emerald-400 font-mono rounded py-1 focus:border-emerald-500 outline-none"
          value={userOdds}
          onChange={(e) => setUserOdds(parseFloat(e.target.value))}
        />

        {/* Live Edge Result */}
        <div className={`text-center font-bold border rounded py-1 ${edge > 0 ? "bg-emerald-900/20 border-emerald-500/50 text-emerald-400" : "bg-zinc-900 border-zinc-800 text-zinc-600"}`}>
          {edge > 0 ? "+" : ""}{edgePercent}%
          {edge > 0 && <div className="text-[9px] text-emerald-600">Bet €{kelly.toFixed(0)}</div>}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-lg">
      {/* Header */}
      <div className="bg-zinc-900/50 p-4 border-b border-zinc-800">
        <div className="text-xs text-zinc-500 uppercase tracking-widest">{data.league}</div>
        <div className="text-lg font-bold">{data.match}</div>
        <div className="flex gap-2 mt-3">
          {["1X2", "DC", "GOALS"].map(tab => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`text-xs px-3 py-1 rounded-full border transition-all ${activeTab === tab ? "bg-emerald-500 text-black border-emerald-500 font-bold" : "border-zinc-700 text-zinc-400 hover:border-zinc-500"}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Header Row */}
        <div className="grid grid-cols-4 gap-2 text-[10px] text-zinc-500 uppercase mb-2 text-center font-bold">
          <div className="text-left">Outcome</div>
          <div>True Prob</div>
          <div>Your Odds</div>
          <div>Edge</div>
        </div>

        {activeTab === "1X2" && (
          <>
            {renderRow("Home", "1", "1")}
            {renderRow("Draw", "X", "X")}
            {renderRow("Away", "2", "2")}
          </>
        )}

        {activeTab === "DC" && (
          <>
            {renderRow("1X (Home/Draw)", "1X", "1X_dummy")} 
            {renderRow("X2 (Draw/Away)", "X2", "X2_dummy")}
            {/* Note: API usually doesn't give DC odds, so these default to 0 until you type them */}
          </>
        )}

        {activeTab === "GOALS" && (
          <>
            {renderRow("Over 2.5", "O2.5", "O2.5")}
            {renderRow("Under 2.5", "U2.5", "U2.5")}
            {renderRow("Over 1.5", "O1.5", "O1.5_dummy")}
            {renderRow("Under 1.5", "U1.5", "U1.5_dummy")}
          </>
        )}
      </div>
    </div>
  );
}