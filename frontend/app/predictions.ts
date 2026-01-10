// app/predictions.ts

interface ModelPrediction {
  home: number; // 0.0 to 1.0
  draw: number;
  away: number;
}

// Key format: "HomeTeam vs AwayTeam" (Exact spelling from API)
export const MODEL_PREDICTIONS: Record<string, ModelPrediction> = {
  // Game 1: Frankfurt vs Dortmund
  // Model Result: Frankfurt strong at home recently vs Dortmund's away form
  "Eintracht Frankfurt vs Borussia Dortmund": {
    home: 0.546, // 54.6%
    draw: 0.207, // 20.7%
    away: 0.246, // 24.6%
  },
  
  // Game 2: Heidenheim vs Köln
  // Model Result: Köln has better underlying stats in the dataset
  "1. FC Heidenheim vs 1. FC Köln": {
    home: 0.230, // 23.0%
    draw: 0.281, // 28.1%
    away: 0.489, // 48.9%
  },

  // Game 3: Bayern vs Dortmund (Classic matchup)
  "Bayern Munich vs Borussia Dortmund": {
    home: 0.815, // 81.5% (Bayern very dominant at home in dataset)
    draw: 0.112,
    away: 0.073,
  },

  // Game 4: RB Leipzig vs Leverkusen
  "RB Leipzig vs Bayer Leverkusen": {
    home: 0.429,
    draw: 0.217,
    away: 0.354,
  }
};