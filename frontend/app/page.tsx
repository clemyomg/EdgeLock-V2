"use client";
import React, { useState, useEffect } from "react";

// ✅ Your Railway URL
const BACKEND_URL = "https://edgelock-v2-production.up.railway.app"; 

export default function EdgeLockPro() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bankroll, setBankroll] = useState(1000);

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
    const interval = setInterval(fetchData, 60000); // 1 min refresh
    return () => clearInterval(interval);
  }, []);

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

  if (loading) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-emerald-500 font-mono animate-pulse">Scanning Bundesliga...</div>;
  if (error) return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-red-500">Connection Failed: {error}</div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-4 font-sans pb-24">
      <div className="flex flex-col gap-4 mb-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-emerald-400 tracking-tighter">EdgeLock<span className="text-white">Pro</span></h1>
          <div className="text-[10px] bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full text-zinc-400">
            {matches.length} Fixtures
          </div>
        </div>
        
        <div className="bg-zinc-900/50 p-3 rounded-lg border border-zinc-800 flex justify-between items-center shadow-lg">
          <label className="text-xs text-zinc-500 uppercase font-bold tracking-wider">Bankroll (€)</label>
          <input 
            type="number" 
            value={bankroll} 
            onChange={(e) => setBankroll(Number(e.target.value))}
            className="bg-transparent text-right text-emerald-400 font-bold text-lg outline-none w-32"
          />
        </div>
      </div>

      {matches.length === 0 ? (
        <div className="flex flex-col items-center justify-center mt-20 text-zinc-600">
          <div className="text-4xl mb-2">⚽</div>
          <div>No Bundesliga fixtures found.</div>
          <div className="text-xs mt-1">Check back later.</div>
        </div>
      ) : (
        <div className="grid gap-8">
          {Object.entries(groupedMatches).map(([dateLabel, games]: [string, any]) => (
            <div key={dateLabel} className={dateLabel === "Today" ? "bg-zinc-900/40 p-3 -m-3 rounded-2xl border border-zinc-800/50" : ""}>
              <h2 className={`text-zinc-500 font-bold uppercase text-[10px] tracking-widest mb-3 pl-1 sticky top-0 py-3 backdrop-blur-md z-10 border-b border-transparent ${dateLabel === "Today" ? "text-emerald-400 border-zinc-800" : ""}`}>
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
      )}
    </div>
  );
}

function MatchCard({ data, bankroll }: { data: any, bankroll: number }) {
  const time = new Date(data.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  const isLive = ["1H", "2H", "HT", "ET", "P"].includes(data.score.status);
  const roundDisplay = data.round ? data.round.replace("Regular Season - ", "MD ") : "";

  // ODDS LOGIC
  const homeOdd = data.market_odds["1"] || 0;
  const awayOdd = data.market_odds["2"] || 0;
  
  // Risk (Orange if > 2.50)
  const homeRisky = homeOdd > 2.5;
  const awayRisky = awayOdd > 2.5;

  const dcHomeOdd = data.market_odds["1X"] || 0;
  const dcAwayOdd = data.market_odds["X2"] || 0;

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-sm hover:border-zinc-700 transition-colors relative">
      
      {/* HEADER */}
      <div className="p-4 pb-2 border-b border-zinc-900/50">
        <div className="flex justify-between items-center mb-3">
           <div className="text-[9px] text-zinc-600 uppercase tracking-widest font-bold">{data.league} <span className="text-zinc-700 font-normal">| {roundDisplay}</span></div>
           {isLive ? (
             <div className="text-red-500 text-[10px] font-bold animate-pulse flex items-center gap-1">
               <span className="w-1.5 h-1.5 bg-red-500 rounded-full inline-block"></span>
               {data.score.time}'
             </div>
           ) : (
             <div className="text-[10px] font-mono text-zinc-500 bg-zinc-900 px-1.5 py-0.5 rounded">{time}</div>
           )}
        </div>

        <div className="flex flex-col gap-1.5 mb-2">
           <div className="flex justify-between items-center">
             <div className="text-sm font-bold text-white">{data.home_team}</div>
             {isLive && <div className="text-lg font-bold text-white">{data.score.goals_h}</div>}
           </div>
           <div className="flex justify-between items-center">
             <div className="text-sm font-bold text-zinc-400">{data.away_team}</div>
             {isLive && <div className="text-lg font-bold text-zinc-400">{data.score.goals_a}</div>}
           </div>
        </div>
      </div>

      {/* ODDS CONTENT */}
      {!data.has_model ? (
        <div className="p-4 text-center text-xs text-zinc-600 italic">Insufficient historical data</div>
      ) : (
        <div className="p-4 pt-2 flex flex-col gap-1">
          
          {/* HOME (1) */}
          <BettingRow 
            label="1" 
            prob={data.probs["1"]} fair={data.fair_odds["1"]} market={homeOdd} 
            bankroll={bankroll} 
            isRisky={homeRisky} 
          />
          
          {/* HOME SAFE (1X) - Only show if Risky or user wants Safe options */}
          {homeRisky && dcHomeOdd > 0 && (
             <BettingRow 
               label="SAFE: 1X" 
               prob={data.probs["1X"]} fair={data.fair_odds["1X"]} market={dcHomeOdd} 
               bankroll={bankroll} 
               highlight={true} 
             />
          )}

          <div className="h-px bg-zinc-900/50 my-1"></div>

          {/* AWAY (2) */}
          <BettingRow 
            label="2" 
            prob={data.probs["2"]} fair={data.fair_odds["2"]} market={awayOdd} 
            bankroll={bankroll} 
            isRisky={awayRisky} 
          />

          {/* AWAY SAFE (X2) */}
          {awayRisky && dcAwayOdd > 0 && (
             <BettingRow 
               label="SAFE: X2" 
               prob={data.probs["X2"]} fair={data.fair_odds["X2"]} market={dcAwayOdd} 
               bankroll={bankroll} 
               highlight={true} 
             />
          )}

        </div>
      )}
    </div>
  );
}

function BettingRow({ label, prob, fair, market, bankroll, highlight, isRisky }: any) {
  const [userOdds, setUserOdds] = useState(market || 0);
  useEffect(() => { if (market > 0) setUserOdds(market); }, [market]);

  const edge = userOdds > 0 ? ((prob / 100) * userOdds) - 1 : 0;
  const kellyFraction = edge > 0 ? (((userOdds - 1) * (prob/100) - (1 - (prob/100))) / (userOdds - 1)) * 0.25 : 0;
  const betAmount = kellyFraction * bankroll;

  return (
    <div className={`grid grid-cols-12 gap-2 items-center mb-1 p-2 rounded transition-all ${highlight ? "bg-emerald-900/10 border border-emerald-500/20" : "hover:bg-zinc-900/40 border border-transparent"}`}>
      
      {/* Label */}
      <div className="col-span-4 flex flex-col justify-center leading-tight">
        <div className={`text-xs font-bold ${highlight ? "text-emerald-400" : isRisky ? "text-orange-400" : "text-zinc-300"}`}>
          {label}
        </div>
      </div>
      
      {/* Fair Odds + Probability */}
      <div className="col-span-3 flex flex-col items-center">
        <div className="text-[8px] text-zinc-600 uppercase">Fair</div>
        <div className="text-xs font-bold text-zinc-400">
           {fair?.toFixed(2)} <span className="text-[9px] text-zinc-600 font-normal">({prob?.toFixed(0)}%)</span>
        </div>
      </div>

      {/* User Input */}
      <div className="col-span-2 flex flex-col items-center">
        <div className="text-[8px] text-zinc-600 uppercase">Bookie</div>
        <input 
          type="number" step="0.01"
          className={`w-12 bg-black/50 border text-center font-bold rounded py-0.5 text-xs outline-none focus:bg-black transition-colors ${isRisky ? "text-orange-400 border-orange-500/30" : "text-white border-zinc-800 focus:border-emerald-500"}`}
          value={userOdds}
          onChange={(e) => setUserOdds(parseFloat(e.target.value))}
        />
      </div>

      {/* Edge & Bet Size */}
      <div className="col-span-3 flex justify-end">
        {edge > 0 ? (
          <div className="flex flex-col items-end">
             <div className="text-emerald-400 text-xs font-bold">+{(edge * 100).toFixed(1)}%</div>
             <div className="text-[10px] text-emerald-100 bg-emerald-500/20 px-1.5 py-px rounded mt-0.5 font-mono">€{betAmount.toFixed(0)}</div>
          </div>
        ) : (
          <div className="text-zinc-800 text-xs">-</div>
        )}
      </div>
    </div>
  );
}