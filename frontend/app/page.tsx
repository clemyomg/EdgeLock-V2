"use client";
import React, { useState, useEffect } from "react";

// ✅ Your Railway URL
const BACKEND_URL = "https://edgelock-v2-production.up.railway.app"; 

export default function EdgeLockPro() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Auto-Refresh every 60 seconds to get new scores
  useEffect(() => {
    const fetchData = () => {
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
          setError(err.message);
          setLoading(false);
        });
    };

    fetchData(); // First load
    const interval = setInterval(fetchData, 60000); // Repeat every 60s
    return () => clearInterval(interval);
  }, []);

  // Group by Date
  const groupedMatches = matches.reduce((acc: any, match) => {
    const date = new Date(match.date);
    let label = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) label = "Today";
    else if (date.toDateString() === tomorrow.toDateString()) label = "Tomorrow";

    if (!acc[label]) acc[label] = [];
    acc[label].push(match);
    return acc;
  }, {});

  if (loading) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-emerald-500 font-mono animate-pulse">Scanning Markets...</div>;
  if (error) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-red-500">Connection Failed: {error}</div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-4 font-sans pb-24">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-emerald-400 tracking-tighter">EdgeLock<span className="text-white">Pro</span></h1>
        <div className="text-[10px] bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full text-zinc-400">
          {matches.length} Games Active
        </div>
      </div>

      <div className="grid gap-8">
        {Object.entries(groupedMatches).map(([dateLabel, games]: [string, any]) => (
          <div key={dateLabel}>
            <h2 className="text-zinc-500 font-bold uppercase text-[10px] tracking-widest mb-3 pl-1 sticky top-0 bg-zinc-950/95 py-3 backdrop-blur-md z-10 border-b border-zinc-900">
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
    </div>
  );
}

function MatchCard({ data }: { data: any }) {
  const [activeTab, setActiveTab] = useState("1X2");
  const time = new Date(data.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

  // LIVE SCORE LOGIC
  const isLive = data.score && (data.score.status === "1H" || data.score.status === "2H" || data.score.status === "HT");
  const isFinished = data.score && (data.score.status === "FT");

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl overflow-hidden shadow-sm hover:border-zinc-700 transition-colors relative">
      
      {/* HEADER WITH SCORE */}
      <div className="p-4 pb-2 flex justify-between items-start">
        <div>
           <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">{data.league}</div>
           <div className="text-md font-bold text-white">{data.match}</div>
        </div>

        {/* Live Badge / Time */}
        <div className="text-right">
          {isLive ? (
             <div className="bg-red-500/20 text-red-500 border border-red-500/50 px-2 py-1 rounded text-xs font-bold animate-pulse">
               {data.score.elapsed}' • {data.score.goals_h}-{data.score.goals_a}
             </div>
          ) : isFinished ? (
             <div className="bg-zinc-800 text-zinc-400 px-2 py-1 rounded text-xs font-bold">
               FT • {data.score.goals_h}-{data.score.goals_a}
             </div>
          ) : (
             <div className="text-[10px] font-mono text-zinc-600 bg-zinc-950 px-2 py-1 rounded">{time}</div>
          )}
        </div>
      </div>

      {/* TABS & ODDS */}
      {!data.has_model ? (
        <div className="px-4 pb-4">
          <div className="bg-zinc-900/50 border border-zinc-800 p-3 rounded text-center text-xs text-zinc-500 italic mt-2">
            ⚠️ Insufficient historical data for this match.
          </div>
        </div>
      ) : (
        <>
          <div className="flex gap-2 px-4 mt-2 overflow-x-auto no-scrollbar">
            {["1X2", "DC", "GOALS"].map(tab => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`text-[10px] uppercase font-bold px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${activeTab === tab ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-zinc-300"}`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="p-4 pt-3">
            {activeTab === "1X2" && (
              <>
                <BettingRow label="Home" prob={data.probs["1"]} fair={data.fair_odds["1"]} market={data.market_odds["1"]} />
                <BettingRow label="Draw" prob={data.probs["X"]} fair={data.fair_odds["X"]} market={data.market_odds["X"]} />
                <BettingRow label="Away" prob={data.probs["2"]} fair={data.fair_odds["2"]} market={data.market_odds["2"]} />
              </>
            )}
            {activeTab === "DC" && (
              <>
                <BettingRow label="1X" prob={data.probs["1X"]} fair={data.fair_odds["1X"]} market={0} />
                <BettingRow label="X2" prob={data.probs["X2"]} fair={data.fair_odds["X2"]} market={0} />
              </>
            )}
            {activeTab === "GOALS" && (
              <>
                <BettingRow label="Over 2.5" prob={data.probs["O2.5"]} fair={data.fair_odds["O2.5"]} market={data.market_odds["O2.5"]} />
                <BettingRow label="Under 2.5" prob={data.probs["U2.5"]} fair={data.fair_odds["U2.5"]} market={data.market_odds["U2.5"]} />
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function BettingRow({ label, prob, fair, market }: { label: string, prob: number, fair: number, market: number }) {
  const [userOdds, setUserOdds] = useState(market || 0);
  useEffect(() => { if (market > 0) setUserOdds(market); }, [market]);
  const edge = userOdds > 0 ? ((prob / 100) * userOdds) - 1 : 0;
  
  return (
    <div className="grid grid-cols-12 gap-2 items-center mb-3 bg-zinc-900/50 p-2 rounded border border-transparent hover:border-zinc-800 transition-all">
      <div className="col-span-3 text-xs font-bold text-zinc-400">{label}</div>
      <div className="col-span-3 flex flex-col items-center border-r border-zinc-800/50">
        <div className="text-[10px] text-zinc-600 uppercase">Fair</div>
        <div className="text-lg font-bold text-amber-400">{fair?.toFixed(2)}</div>
        <div className="text-[9px] text-zinc-500">{prob?.toFixed(0)}%</div>
      </div>
      <div className="col-span-3 flex flex-col items-center">
        <div className="text-[10px] text-zinc-600 uppercase">Bookie</div>
        <input 
          type="number" step="0.01"
          className="w-16 bg-zinc-950 border border-zinc-800 text-center text-white font-bold rounded py-1 text-sm focus:border-emerald-500 outline-none"
          value={userOdds}
          onChange={(e) => setUserOdds(parseFloat(e.target.value))}
        />
      </div>
      <div className="col-span-3 flex justify-end">
        <div className={`w-full text-center font-bold text-xs py-2 rounded ${edge > 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-800/50 text-zinc-600"}`}>
          {edge > 0 ? "+" : ""}{(edge * 100).toFixed(1)}%
        </div>
      </div>
    </div>
  );
}