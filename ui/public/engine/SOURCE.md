# Stockfish in the browser

`stockfish-19-lite-single.js` and `.wasm` are copied unchanged from the npm package
[`stockfish@19.0.1`](https://www.npmjs.com/package/stockfish/v/19.0.1) (stockfish.js by Chess.com,
based on [Stockfish](https://github.com/official-stockfish/Stockfish) 19). They are licensed under the
GNU General Public License v3; the full text is in `COPYING.txt` next to this file.

Corresponding source:
- stockfish.js 19.0.1: https://github.com/nmrugg/stockfish.js/tree/v19.0.1
- Stockfish 19: https://github.com/official-stockfish/Stockfish/tree/sf_19

Chess Habits runs the engine as a separate program in a Web Worker and talks to it only through UCI
text messages (see `ui/src/deep/engine.ts`).
