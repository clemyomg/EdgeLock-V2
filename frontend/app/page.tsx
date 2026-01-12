"use client";
import React, { useState, useEffect } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"; 

const LEAGUES = ["Bundesliga", "Premier League", "La Liga", "Serie A", "Ligue 1"];
const THEMES = {
  dark: "bg-zinc-950 text-white",
  light: "bg-gray-100 text-gray-900",
};

export default function EdgeLockPro() {
  const [matches, setMatches] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [activeLeague, setActiveLeague] = useState("Bundesliga"); 
  const [view, setView] = useState<"upcoming" | "history">("upcoming");
  const [globalTab, setGlobalTab] = useState<"winner" | "handicap" | "goals">("winner"); 
  const [bankroll, setBankroll] = useState(1000);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetch(`${BACKEND_URL}/live-edges`)
      .then(res => res.json())
      .then(data => {
        if(data.matches) setMatches(data.matches);
        if(data.history) setHistory(data.history);
        setLoading(false);
      })
      .catch(e => setLoading(false));
  }, []);

  const filteredMatches = matches.filter(m => m.league === activeLeague);

  const grouped = filteredMatches.reduce((acc: any, m) => {
    const d = new Date(m.date);
    const roundShort = m.round ? m.round.replace("Regular Season - ", "MD ") : "";
    const dateStr = d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
    const label = `${dateStr} • ${roundShort}`;
    if (!acc[label]) acc[label] = [];
    acc[label].push(m);
    return acc;
  }, {});

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");
  const baseClass = THEMES[theme];
  const cardClass = theme === "dark" ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200 shadow-sm";

  if (loading) return (
    <div className={`min-h-screen flex flex-col items-center justify-center ${baseClass}`}>
       <div className="w-10 h-10 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mb-4"></div>
       <div className="text-xs font-bold tracking-widest uppercase animate-pulse">Scanning Market...</div>
    </div>
  );

  return (
    <div className={`min-h-screen font-sans pb-24 transition-colors duration-300 ${baseClass}`}>
      <style jsx global>{`
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${theme === 'dark' ? '#3f3f46' : '#d1d5db'}; border-radius: 10px; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>

      {/* HEADER */}
      <div className={`sticky top-0 z-50 p-4 border-b backdrop-blur-md flex justify-between items-center ${theme === "dark" ? "bg-zinc-950/80 border-zinc-900" : "bg-white/80 border-gray-200"}`}>
         <div className="flex flex-col">
            <div className="text-[10px] font-mono opacity-60">{currentTime.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</div>
            <div className="text-[10px] font-bold opacity-80">{currentTime.toLocaleDateString([], {month:'short', day:'numeric'})}</div>
         </div>
         <div className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center">
             <h1 className="text-xl font-black tracking-tighter italic">EdgeLock<span className="text-emerald-500">Pro</span></h1>
         </div>
         <div className="flex gap-3 items-center">
            <div className={`flex items-center px-2 py-1 rounded text-xs font-bold ${theme === "dark" ? "bg-zinc-900" : "bg-gray-200"}`}>
               <span className="text-emerald-500 mr-1">€</span>{bankroll}
            </div>
            <button onClick={toggleTheme} className="text-xl opacity-70 hover:opacity-100">{theme === "dark" ? "☀️" : "🌙"}</button>
         </div>
      </div>

      {/* LEAGUE TABS */}
      <div className={`py-3 px-4 border-b ${theme === "dark" ? "border-zinc-900" : "border-gray-200"}`}>
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {LEAGUES.map(league => (
            <button key={league} onClick={() => setActiveLeague(league)}
              className={`px-4 py-1.5 rounded-full text-[10px] font-bold tracking-wide whitespace-nowrap transition-all border ${activeLeague === league ? "bg-emerald-500 text-white border-emerald-500 shadow-lg shadow-emerald-500/20" : theme === "dark" ? "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-700" : "bg-white text-gray-500 border-gray-200 hover:border-gray-300"}`}>
              {league}
            </button>
          ))}
        </div>
      </div>

      {/* VIEW TOGGLE */}
      <div className="flex justify-center my-4">
        <div className={`flex p-1 rounded-full ${theme === "dark" ? "bg-zinc-900" : "bg-gray-200"}`}>
           <button onClick={() => setView("upcoming")} className={`px-4 py-1 rounded-full text-xs font-bold transition-all ${view === "upcoming" ? "bg-emerald-500 text-white shadow" : "opacity-50"}`}>Matches</button>
           <button onClick={() => setView("history")} className={`px-4 py-1 rounded-full text-xs font-bold transition-all ${view === "history" ? "bg-emerald-500 text-white shadow" : "opacity-50"}`}>Log</button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      {view === "upcoming" ? (
        <div className="flex flex-col gap-8 px-4 py-6">
           {filteredMatches.length === 0 ? (
              <div className="flex flex-col items-center justify-center mt-10 opacity-50">
                 <div className="text-4xl mb-2">🏟️</div>
                 <div className="text-sm">No {activeLeague} games found.</div>
                 <div className="text-xs mt-2 text-emerald-500">Checking Offline Database...</div>
              </div>
           ) : (
             Object.keys(grouped).map(label => (
               <div key={label}>
                 <h3 className={`text-xs font-bold uppercase tracking-widest mb-4 pl-2 border-l-2 ${theme === "dark" ? "border-emerald-500 text-emerald-500" : "border-emerald-600 text-emerald-600"}`}>{label}</h3>
                 
                 <div className="flex flex-nowrap overflow-x-auto gap-4 pb-4 snap-x md:grid md:grid-cols-2 lg:grid-cols-3 md:overflow-visible md:pb-0">
                    {grouped[label].map((m: any) => (
                      <div key={m.id} className="snap-start shrink-0 w-[85vw] md:w-auto h-full flex flex-col">
                         <MatchCard 
                            data={m} 
                            theme={theme} 
                            cardClass={cardClass} 
                            bankroll={bankroll} 
                            globalTab={globalTab} 
                            setGlobalTab={setGlobalTab} 
                         />
                      </div>
                    ))}
                 </div>
               </div>
             ))
           )}
        </div>
      ) : (
        <div className="p-4 max-w-2xl mx-auto">
           <h2 className="text-xl font-bold mb-4">Performance Log</h2>
           <div className={`rounded-xl overflow-hidden border ${theme === "dark" ? "border-zinc-800" : "border-gray-200"}`}>
              <div className="p-4 text-center opacity-50">Log active once bets settle.</div>
           </div>
        </div>
      )}
    </div>
  );
}

function MatchCard({ data, theme, cardClass, bankroll, globalTab, setGlobalTab }: any) {
  const isLive = ["1H", "2H", "HT", "ET", "P"].includes(data.score.status);
  const matchTime = new Date(data.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: false});

  return (
    <div className={`rounded-2xl border p-4 relative transition-colors h-full flex flex-col ${cardClass}`}>
      <div className="flex items-center gap-2 mb-2 opacity-70">
         {data.country_flag && <img src={data.country_flag} className="w-4 h-4 rounded-full shadow-sm" />}
         <span className="text-[10px] font-bold uppercase tracking-wider">{data.league}</span>
         {isLive && <span className="ml-auto bg-red-500 text-white text-[9px] px-2 py-0.5 rounded-full animate-pulse">LIVE {data.score.time}'</span>}
      </div>

      {!isLive && <div className={`text-center text-[10px] font-mono font-bold mb-1 ${theme === "dark" ? "text-zinc-500" : "text-gray-400"}`}>{matchTime}</div>}

      <div className="flex justify-between items-center mb-6">
         <div className="flex flex-col items-center w-1/3 text-center">
            {data.home_logo && <img src={data.home_logo} className="w-12 h-12 object-contain mb-2" />}
            <span className="text-sm font-bold leading-tight">{data.home_team}</span>
            {data.predicted_xg && <span className="text-xs text-emerald-500 font-mono mt-1 font-bold">{data.predicted_xg.home} xG</span>}
         </div>

         <div className="flex flex-col items-center">
            {isLive ? (
               <div className="text-3xl font-black font-mono tracking-tighter">{data.score.goals_h}-{data.score.goals_a}</div>
            ) : data.most_likely_score ? (
               <div className={`text-4xl font-black tracking-[0.2em] opacity-30 ${theme==="dark"?"text-white":"text-black"}`}>
                  {data.most_likely_score.replace("-", ":")}
               </div>
            ) : (
               <span className="text-xs font-bold opacity-30 bg-gray-500/10 px-2 py-1 rounded">VS</span>
            )}
         </div>

         <div className="flex flex-col items-center w-1/3 text-center">
            {data.away_logo && <img src={data.away_logo} className="w-12 h-12 object-contain mb-2" />}
            <span className="text-sm font-bold leading-tight">{data.away_team}</span>
            {data.predicted_xg && <span className="text-xs text-emerald-500 font-mono mt-1 font-bold">{data.predicted_xg.away} xG</span>}
         </div>
      </div>

      {!isLive && data.has_model && (
        <div className={`flex justify-center gap-4 mb-4 border-b ${theme==="dark"?"border-zinc-800":"border-gray-200"}`}>
           <button onClick={()=>setGlobalTab("winner")} className={`pb-2 text-[10px] font-bold uppercase transition-all ${globalTab==="winner" ? "border-b-2 border-emerald-500 text-emerald-500" : "opacity-40"}`}>Winner</button>
           <button onClick={()=>setGlobalTab("handicap")} className={`pb-2 text-[10px] font-bold uppercase transition-all ${globalTab==="handicap" ? "border-b-2 border-emerald-500 text-emerald-500" : "opacity-40"}`}>H'cap</button>
           <button onClick={()=>setGlobalTab("goals")} className={`pb-2 text-[10px] font-bold uppercase transition-all ${globalTab==="goals" ? "border-b-2 border-emerald-500 text-emerald-500" : "opacity-40"}`}>Goals</button>
        </div>
      )}

      <div className="flex-1 flex flex-col justify-end">
        {!isLive && data.has_model && (
           <div className="flex flex-col gap-3">
              {globalTab === "winner" && <WinnerTab data={data} theme={theme} bankroll={bankroll} />}
              {globalTab === "handicap" && <HandicapTab data={data} theme={theme} bankroll={bankroll} />}
              {globalTab === "goals" && <GoalsTab data={data} theme={theme} bankroll={bankroll} />}
           </div>
        )}
        {!data.has_model && !isLive && <div className="text-center text-xs opacity-40 italic mt-2">Waiting for Model Data...</div>}
      </div>
    </div>
  );
}

function WinnerTab({ data, theme, bankroll }: any) {
  return (
    <>
      <div className="grid grid-cols-3 gap-1">
         <BetRow label="1" prob={data.probs["1"]} odd={data.market_odds["1"]} theme={theme} bankroll={bankroll} />
         <BetRow label="X" prob={data.probs["X"]} odd={data.market_odds["X"]} theme={theme} bankroll={bankroll} />
         <BetRow label="2" prob={data.probs["2"]} odd={data.market_odds["2"]} theme={theme} bankroll={bankroll} />
      </div>
      <div className="grid grid-cols-2 gap-1">
         <BetRow label="1X" prob={data.probs["1X"]} odd={data.market_odds["1X"]} theme={theme} bankroll={bankroll} isSafe={true} />
         <BetRow label="X2" prob={data.probs["X2"]} odd={data.market_odds["X2"]} theme={theme} bankroll={bankroll} isSafe={true} />
      </div>
    </>
  )
}

function HandicapTab({ data, theme, bankroll }: any) {
    const handicaps = data.market_odds["Handicaps"] || [];
    
    // Sort Home vs Away
    const homeH = handicaps.filter((h:any) => h.label.includes("Home")).sort((a:any,b:any) => a.odd - b.odd);
    const awayH = handicaps.filter((h:any) => h.label.includes("Away")).sort((a:any,b:any) => a.odd - b.odd);

    return (
        <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex flex-col gap-1">
                <div className="text-center opacity-50 font-bold mb-1">Home</div>
                {homeH.length > 0 ? homeH.slice(0,4).map((h:any, i:number) => {
                    const probKey = h.label.replace(" ", ""); 
                    return <BetRow key={i} label={h.label.replace("Home ", "")} prob={data.probs[probKey]} odd={h.odd} theme={theme} bankroll={bankroll} />
                }) : <div className="opacity-30 text-center">-</div>}
            </div>
            <div className="flex flex-col gap-1">
                <div className="text-center opacity-50 font-bold mb-1">Away</div>
                {awayH.length > 0 ? awayH.slice(0,4).map((h:any, i:number) => {
                    const probKey = h.label.replace(" ", ""); 
                    return <BetRow key={i} label={h.label.replace("Away ", "")} prob={data.probs[probKey]} odd={h.odd} theme={theme} bankroll={bankroll} />
                }) : <div className="opacity-30 text-center">-</div>}
            </div>
        </div>
    )
}

function GoalsTab({ data, theme, bankroll }: any) {
    const goals = data.market_odds["Goals"] || {};
    const lines = ["1.5", "2.5", "3.5", "4.5"];

    return (
        <div className="flex flex-col gap-1">
            <div className="grid grid-cols-3 text-[9px] uppercase font-bold opacity-50 text-center mb-1">
                <div>Total</div>
                <div>Under</div>
                <div>Over</div>
            </div>
            {lines.map(line => (
                <div key={line} className="grid grid-cols-3 gap-1 items-center">
                    <div className="text-center font-bold text-xs">{line}</div>
                    <BetRow label="U" prob={data.probs[`Under${line}`]} odd={goals[line]?.Under} theme={theme} bankroll={bankroll} />
                    <BetRow label="O" prob={data.probs[`Over${line}`]} odd={goals[line]?.Over} theme={theme} bankroll={bankroll} />
                </div>
            ))}
        </div>
    )
}

function BetRow({ label, prob, odd, theme, bankroll, isSafe }: any) {
  const [val, setVal] = useState(odd || 0);
  useEffect(() => setVal(odd), [odd]);
  
  const handleInput = (e: any) => {
    let v = e.target.value.replace(',', '.');
    if ((v.match(/\./g) || []).length > 1) return;
    setVal(v);
  }
  
  const numVal = parseFloat(val) || 0;
  const edge = numVal > 0 ? ((prob/100) * numVal) - 1 : 0;
  const stake = edge > 0 ? ((((numVal-1)*(prob/100)-(1-(prob/100))) / (numVal-1)) * 0.25 * bankroll) : 0;
  const hasValue = edge > 0;
  const probDisplay = prob ? `${prob.toFixed(0)}%` : "-";

  return (
     <div className={`flex flex-col rounded-lg overflow-hidden transition-all ${hasValue ? "bg-emerald-500/10 ring-1 ring-emerald-500/50 shadow-lg shadow-emerald-500/10" : theme==="dark" ? "bg-zinc-800/50 hover:bg-zinc-800 h-9" : "bg-white hover:bg-gray-50 border border-gray-100 h-9"}`}>
        
        <div className="flex items-center justify-between px-2 h-9">
            <div className={`w-1/3 text-[10px] font-bold truncate ${isSafe ? "text-emerald-500" : ""}`}>{label}</div>
            
            <div className="w-1/3 text-center flex items-center justify-center">
               <span className={`text-[10px] font-bold ${theme==="dark"?"text-zinc-400":"text-gray-600"}`}>{probDisplay}</span>
            </div>

            <div className="w-1/3 flex justify-end">
               <input type="text" inputMode="decimal" value={val > 0 ? val : ""} placeholder="-" onChange={handleInput} 
                 className={`w-10 text-center text-[10px] font-bold rounded py-0.5 outline-none focus:ring-1 focus:ring-emerald-500 transition-all ${theme==="dark"?"bg-black/50 text-white placeholder-zinc-700":"bg-gray-100 text-black placeholder-gray-400"}`} />
            </div>
        </div>
        
        {hasValue && (
          <div className="bg-emerald-500 text-emerald-950 px-2 py-1 flex justify-between items-center text-[9px] font-black uppercase tracking-wide">
             <div className="flex items-center gap-1 italic">
                <span>⚡ Lock:</span>
                <span className="text-white drop-shadow-sm">+{(edge*100).toFixed(1)}%</span>
             </div>
             <div className="flex items-center gap-1">
                <span>Bet:</span>
                <span className="bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded-sm">€{stake.toFixed(0)}</span>
             </div>
          </div>
        )}
     </div>
  )
}