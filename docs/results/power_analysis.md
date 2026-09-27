# Statistical resolution of completed experiments (descriptive)

**Descriptive only.** This report does not change any verdict, qualification rule or threshold. It shows the smallest true mean edge per trade (bps) that each completed experiment would have detected with 80% probability, per qualification component (forced track, test segments). The design MDE is the largest component, since all must pass.

| experiment | symbol | trades | windows | trades/window | observed bps | cost bps | sd bps | days | MDE t>=2 (IID) | MDE t>=2 (day-clustered) | MDE windows>=60% | MDE drift p<=0.05 | **design MDE** | MDE / cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trend_continuation | BTCUSD | 117 | 6 | 20 | -13.2 | 5.6 | 427 | 114 | 112.1 | 113.4 | 59.6 | - | **113.4** | 20.2x |
| trend_continuation | EURUSD | 89 | 7 | 13 | -7.6 | 1.3 | 57 | 86 | 17.2 | 17.5 | 11.9 | - | **17.5** | 13.6x |
| trend_continuation | XAUUSD | 104 | 7 | 15 | +9.2 | 1.2 | 236 | 101 | 65.9 | 61.1 | 45.6 | - | **61.1** | 49.6x |
| sweep_reversal_long | BTCUSD | 285 | 6 | 48 | -13.9 | 6.4 | 184 | 270 | 31.0 | 31.3 | 16.5 | 25.4 | **31.3** | 4.9x |
| sweep_reversal_long | EURUSD | 329 | 7 | 47 | -1.6 | 1.3 | 23 | 286 | 3.6 | 3.7 | 2.5 | 3.0 | **3.7** | 2.9x |
| sweep_reversal_long | XAUUSD | 255 | 7 | 36 | -0.2 | 1.2 | 92 | 227 | 16.3 | 16.1 | 11.3 | 13.3 | **16.1** | 12.9x |
| sweep_reversal_short | BTCUSD | 498 | 6 | 83 | -1.7 | 7.0 | 129 | 407 | 16.4 | 15.8 | 8.7 | 14.8 | **15.8** | 2.2x |
| sweep_reversal_short | EURUSD | 482 | 7 | 69 | -1.9 | 1.3 | 24 | 394 | 3.1 | 3.1 | 2.2 | 2.4 | **3.1** | 2.5x |
| sweep_reversal_short | XAUUSD | 450 | 7 | 64 | -3.1 | 1.3 | 47 | 365 | 6.2 | 6.4 | 4.3 | 5.5 | **6.4** | 5.0x |
| vol_expansion_long | BTCUSD | 211 | 6 | 35 | +15.8 | 6.4 | 143 | 195 | 28.1 | 28.3 | 14.9 | 27.2 | **28.3** | 4.4x |
| vol_expansion_long | EURUSD | 225 | 7 | 32 | +0.7 | 1.3 | 33 | 208 | 6.3 | 6.3 | 4.4 | 4.8 | **6.3** | 4.9x |
| vol_expansion_long | XAUUSD | 159 | 7 | 23 | +21.5 | 1.3 | 118 | 156 | 26.5 | 26.5 | 18.4 | 19.9 | **26.5** | 20.0x |
| vol_expansion_short | BTCUSD | 189 | 6 | 32 | +7.1 | 6.1 | 154 | 174 | 31.8 | 32.3 | 16.9 | 32.1 | **32.3** | 5.3x |
| vol_expansion_short | EURUSD | 207 | 7 | 30 | -1.5 | 1.3 | 34 | 199 | 6.8 | 6.7 | 4.7 | 5.1 | **6.7** | 5.3x |
| vol_expansion_short | XAUUSD | 189 | 7 | 27 | -11.7 | 1.3 | 72 | 171 | 14.9 | 15.2 | 10.3 | 15.3 | **15.3** | 11.6x |
| replication_r1_pooled | ETH+LTC+XRP | 286 | 6 | 48 | -26.3 | 27.0 | 307 | 244 | 51.6 | 55.9 | 27.4 | 46.5 | **55.9** | 2.1x |
