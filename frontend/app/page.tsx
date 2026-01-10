"use client";
import React, { useState, useEffect } from "react";

// ✅ Your Railway URL
const BACKEND_URL = "https://edgelock-v2-production.up.railway.app"; 

export default function EdgeLockPro() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bankroll, setBankroll] = useState(1000); // 💰 Default Bankroll

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

    fetchData();
    const interval = setInterval(fetchData, 60000);
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
      {/* HEADER & BANKROLL */}
      <div className="flex flex-col gap-4 mb-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-emerald-400 tracking-tighter">EdgeLock<span className="text-white">Pro</span></h1>
          <div className="text-[10px] bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full text-zinc-400">
            {matches.length} Games
          </div>
        </div>
        
        {/* 💰 BANKROLL INPUT */}
        <div className="bg-zinc-900/50 p-3 rounded-lg border border-zinc-800 flex justify-between items-center">
          <label className="text-xs text-zinc-500 uppercase font-bold">Bankroll (€)</label>
          <input 
            type="number" 
            value={bankroll} 
            onChange={(e) => setBankroll(Number(e.target.value))}
            className="bg-transparent text-right text-emerald-400 font-bold outline-none w-24"
          />
        </div>
      </div>

      <div className="grid gap-8">
        {Object.entries(groupedMatches).map(([dateLabel, games]: [string, any]) => (
          <div key={dateLabel} className={dateLabel === "Today" ? "bg-zinc-900/30 p-2 -m-2 rounded-xl" : ""}>
            <h2 className={`text-zinc-500 font-bold uppercase text-[10px] tracking-widest mb-3 pl-1 sticky top-0 py-3 backdrop-blur-md z-10 border-b border-zinc-800 ${dateLabel === "Today" ? "text-emerald-500" : ""}`}>
              {dateLabel}
            </h2>
            <div className="grid gap-4">
              {games.map((m: any) => (
                <MatchCard key={m.id} data={m} bankroll={bankroll} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MatchCard({ data, bankroll }: { data: any, bankroll: number }) {
  const [activeTab, setActiveTab] = useState("1X2");
  const time = new Date(data.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

  // LIVE SCORE LOGIC
  const isLive = data.score && (data.score.status === "1H" || data.score.status === "2H" || data.score.status === "HT");
  const scoreDisplay = data.score ? `${data.score.goals_h}-${data.score.goals_a}` : "";
  const roundDisplay = data.round ? data.round.replace("Regular Season - ", "MD ") : "";

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-sm hover:border-zinc-700 transition-colors relative">
      
      {/* HEADER: STACKED TEAMS */}
      <div className="p-4 pb-2 flex justify-between items-start">
        <div className="flex flex-col gap-1 w-full">
           <div className="flex justify-between items-center w-full">
             <div className="text-[9px] text-zinc-600 uppercase tracking-widest">{data.league} <span className="text-zinc-700">• {roundDisplay}</span></div>
             
             {/* TIME / LIVE BADGE */}
             {isLive ? (
               <div className="text-red-500 text-[10px] font-bold animate-pulse">{data.score.elapsed}' • {scoreDisplay}</div>
             ) : (
               <div className="text-[10px] font-mono text-zinc-600">{time}</div>
             )}
           </div>

           {/* TEAMS STACKED */}
           <div className="mt-2">
             <div className="text-md font-bold text-white flex justify-between">
               {data.home_team} 
               {isLive && <span className="text-emerald-400">{data.score.goals_h}</span>}
             </div>
             <div className="text-md font-bold text-zinc-400 flex justify-between">
               {data.away_team}
               {isLive && <span className="text-emerald-400">{data.score.goals_a}</span>}
             </div>
           </div>
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
          <div className="flex gap-2 px-4 mt-2 mb-2 overflow-x-auto no-scrollbar">
            {["1X2", "GOALS"].map(tab => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`text-[10px] uppercase font-bold px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${activeTab === tab ? "bg-zinc-800 text-white" : "text-zinc-600 hover:text-zinc-300"}`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="p-4 pt-0">
            {activeTab === "1X2" && (
              <>
                {/* 1X2 + DC (Draw removed, 1X/X2 added) */}
                <BettingRow label="Home Win (1)" prob={data.probs["1"]} fair={data.fair_odds["1"]} market={data.market_odds["1"]} bankroll={bankroll} />
                <BettingRow label="Away Win (2)" prob={data.probs["2"]} fair={data.fair_odds["2"]} market={data.market_odds["2"]} bankroll={bankroll} />
                <div className="h-px bg-zinc-900 my-2"></div>
                <BettingRow label="Double Chance 1X" prob={data.probs["1X"]} fair={data.fair_odds["1X"]} market={0} bankroll={bankroll} highlight={true} />
                <BettingRow label="Double Chance X2" prob={data.probs["X2"]} fair={data.fair_odds["X2"]} market={0} bankroll={bankroll} highlight={true} />
              </>
            )}
            {activeTab === "GOALS" && (
              <>
                <BettingRow label="Over 2.5" prob={data.probs["O2.5"]} fair={data.fair_odds["O2.5"]} market={data.market_odds["O2.5"]} bankroll={bankroll} />
                <BettingRow label="Under 2.5" prob={data.probs["U2.5"]} fair={data.fair_odds["U2.5"]} market={data.market_odds["U2.5"]} bankroll={bankroll} warning="⚠️ High Volatility" />
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function BettingRow({ label, prob, fair, market, bankroll, highlight, warning }: { label: string, prob: number, fair: number, market: number, bankroll: number, highlight?: boolean, warning?: string }) {
  const [userOdds, setUserOdds] = useState(market || 0);
  useEffect(() => { if (market > 0) setUserOdds(market); }, [market]);

  const edge = userOdds > 0 ? ((prob / 100) * userOdds) - 1 : 0;
  
  // 💰 Kelly Criterion Calculation
  const kellyFraction = edge > 0 ? (((userOdds - 1) * (prob/100) - (1 - (prob/100))) / (userOdds - 1)) * 0.25 : 0;
  const betAmount = kellyFraction * bankroll;

  return (
    <div className={`grid grid-cols-12 gap-2 items-center mb-2 p-2 rounded border border-transparent transition-all ${highlight ? "bg-zinc-900/80 border-zinc-800" : "hover:bg-zinc-900/30"}`}>
      
      {/* Label */}
      <div className="col-span-4 flex flex-col justify-center">
        <div className={`text-xs font-bold ${highlight ? "text-white" : "text-zinc-400"}`}>{label}</div>
        {warning && <div className="text-[8px] text-orange-500 font-bold mt-0.5">{warning}</div>}
      </div>
      
      {/* FAIR ODDS */}
      <div className="col-span-3 flex flex-col items-center border-r border-zinc-800/50">
        <div className="text-[9px] text-zinc-600 uppercase">Fair</div>
        <div className="text-sm font-bold text-amber-400">{fair?.toFixed(2)}</div>
      </div>

      {/* USER INPUT */}
      <div className="col-span-2 flex flex-col items-center">
        <div className="text-[9px] text-zinc-600 uppercase">Odd</div>
        <input 
          type="number" step="0.01"
          className="w-12 bg-black border border-zinc-800 text-center text-white font-bold rounded py-1 text-xs focus:border-emerald-500 outline-none"
          value={userOdds}
          onChange={(e) => setUserOdds(parseFloat(e.target.value))}
        />
      </div>

      {/* EDGE / BET SIZE */}
      <div className="col-span-3 flex justify-end">
        {edge > 0 ? (
          <div className="w-full text-center bg-emerald-900/30 border border-emerald-500/30 rounded py-1">
            <div className="text-emerald-400 text-xs font-bold">+{(edge * 100).toFixed(1)}%</div>
            <div className="text-[9px] text-emerald-200 font-mono">€{betAmount.toFixed(0)}</div>
          </div>
        ) : (
          <div className="w-full text-center py-1 text-zinc-700 text-xs">-</div>
        )}
      </div>
    </div>
  );
}