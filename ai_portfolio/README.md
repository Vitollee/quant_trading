{
  "name": "AI 模拟投资组合",
  "name_en": "AI Simulated Portfolio",
  "description": "虾虾AI量化交易模拟组合，包含长线、波段(Swing)、日内交易(Day Trade)三种策略",
  "version": "1.0.0",
  "created_date": "2026-03-19",
  "author": "虾虾 🦐",
  
  "strategies": {
    "longterm": {
      "description": "长线价值投资 (1年以上)",
      "folder": "longterm/",
      "allocation": "60%"
    },
    "swing": {
      "description": "波段交易 (2-30天)",
      "folder": "swing/",
      "allocation": "30%"
    },
    "daytrade": {
      "description": "日内交易 (当日平仓)",
      "folder": "daytrade/",
      "allocation": "10%"
    }
  },
  
  "data_sources": {
    "hk_stocks": "Futu OpenD",
    "us_stocks": "Finnhub + Yahoo Finance",
    "gold": "Yahoo Finance (GLD ETF)"
  },
  
  "rules": {
    "stop_loss": "-3% 必须止损",
    "take_profit_swing": "+8% 可考虑止盈",
    "take_profit_day": "+5% 当日平仓",
    "max_single_position": "20% 单只仓位限制"
  },
  
  "contact": {
    "whatsapp": "+85265809471"
  }
}
