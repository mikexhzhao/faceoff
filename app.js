(function(){
  const { useEffect, useMemo, useRef, useState } = React;

  // ---- Types (documentation) ----
  // Problem: { id:number, q:string, answer:string|number, image?:string }
  // ProblemSet: { name:string, problems: Problem[] }
  // question_bank.json schema:
  // { "sets": [ "set1.json", "set2.json" ] }
  // Each referenced file has schema:
  // { "name": "Set Name", "problems": [ { "q": "...", "answer": "...", "image": "file.png" } ] }

  // Sound effects (optional)
  class Sounder {
    constructor(){ this.ctx = null; }
    ensure(){ if (!this.ctx) this.ctx = new (window.AudioContext || window.webkitAudioContext)(); }
    tone(freq, dur = 0.15, type = "sine", gain = 0.06) {
      try {
        this.ensure();
        const ctx = this.ctx;
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = type;
        o.frequency.value = freq;
        g.gain.value = gain;
        o.connect(g); g.connect(ctx.destination);
        o.start(); o.stop(ctx.currentTime + dur);
      } catch {}
    }
    tick(){ this.tone(1200, 0.06, "square", 0.03); }
    start(){ this.tone(520,0.12,"triangle"); setTimeout(()=>this.tone(680,0.12,"triangle"),120); setTimeout(()=>this.tone(840,0.12,"triangle"),240); }
    end(){ this.tone(360,0.12,"triangle"); setTimeout(()=>this.tone(540,0.12,"triangle"),120); setTimeout(()=>this.tone(720,0.2,"triangle"),240); }
  }
  const S = new Sounder();

  function shuffle(arr){ const a=[...arr]; for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; }

  function App(){
    const [loadedUrl, setLoadedUrl] = useState(null); // URL used to fetch the bank (for resolving relative image paths)
    const [sets, setSets] = useState([]);
    const [activeSetIdx, setActiveSetIdx] = useState(0);
    const activeSet = sets[activeSetIdx] || { name: "—", problems: [] };
    const bank = activeSet.problems || [];

    const [questionTime, setQuestionTime] = useState(45);
    const [rounds, setRounds] = useState(1);
    const [order, setOrder] = useState([]);
    const [index, setIndex] = useState(0);
    const [started, setStarted] = useState(false);
    const [reveal, setReveal] = useState(false);
    const [paused, setPaused] = useState(false);
    const [timeLeft, setTimeLeft] = useState(questionTime);
    const [gotoValue, setGotoValue] = useState("");
    const [fontSize, setFontSize] = useState(36);

    // Players
    const [players, setPlayers] = useState([]);
    const [newPlayerName, setNewPlayerName] = useState("");

    // Music (local file via <input> still works on Pages)
    const [bgUrl, setBgUrl] = useState(null);
    const [bgLoop, setBgLoop] = useState(true);
    const [bgVol, setBgVol] = useState(0.3);
    const [bgPlaying, setBgPlaying] = useState(false);
    const audioRef = useRef(null);
    const questionRef = useRef(null);
    const answerRef = useRef(null);

    // Fetch question bank on mount
    useEffect(() => {
      const url = new URL("./question_bank.json", document.baseURI).toString();
      setLoadedUrl(url);
      fetch(url, { cache: "no-cache" })
        .then(r => {
          if (!r.ok) throw new Error("Failed to load question_bank.json");
          return r.json();
        })
        .then(data => {
          const files = Array.isArray(data.sets) ? data.sets : [];
          return Promise.all(files.map(f =>
            fetch(new URL(f, url), { cache: "no-cache" })
              .then(r => {
                if (!r.ok) throw new Error("Failed to load " + f);
                return r.json();
              })
              .then(s => ({
                name: String(s.name || "Untitled Set"),
                problems: (Array.isArray(s.problems) ? s.problems : [])
                  .map((p, i) => ({
                    id: i + 1,
                    q: String(p.q ?? p.question ?? "").trim(),
                    answer: (p.answer ?? p.ans),
                    image: (p.image ?? p.img ?? "").trim()
                  }))
                  .filter(p => p.q && (p.answer !== undefined && String(p.answer).length > 0))
              }))
          ));
        })
        .then(parsedSets => {
          setSets(parsedSets);
          setActiveSetIdx(0);
        })
        .catch(err => {
          console.error(err);
          alert("Could not load question_bank.json or one of its sets. Ensure all files exist in the same folder.");
        });
    }, []);

    // When set changes, reset round/order
    useEffect(() => {
      const size = bank.length || 1;
      setRounds(size);
      setOrder(shuffle([...Array(size).keys()]));
      setIndex(0);
      setReveal(false);
      setStarted(false);
      setPaused(false);
      setTimeLeft(questionTime);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeSetIdx, sets.length]);

    // Timer logic
    useEffect(() => { setTimeLeft(questionTime); }, [questionTime, started]);
    useEffect(() => {
      if(!started || paused) return;
      if(timeLeft <= 0) return;
      const t = setTimeout(() => {
        const next = timeLeft - 1;
        if (next <= 5 && next > 0) S.tick();
        setTimeLeft(next);
        if (next <= 0) S.end();
      }, 1000);
      return () => clearTimeout(t);
    }, [started, paused, timeLeft]);

    useEffect(() => { if (audioRef.current) audioRef.current.volume = bgVol; }, [bgVol]);

    function startGame(){ setIndex(0); setReveal(false); setStarted(true); setPaused(false); setTimeLeft(questionTime); S.start(); }
    function nextQuestion(){
      if(index + 1 >= Math.min(rounds, order.length)){ setStarted(false); return; }
      setIndex(i => i + 1); setReveal(false); setPaused(false); setTimeLeft(questionTime); S.start();
    }
    function resetTimer(){ setTimeLeft(questionTime); }
    function gotoQuestion(){
      const n = parseInt(gotoValue, 10);
      if(!isNaN(n) && n >= 1 && n <= Math.min(rounds, order.length)){
        setIndex(n - 1);
        setReveal(false);
        setPaused(false);
        setTimeLeft(questionTime);
        setStarted(true);
        setGotoValue("");
        S.start();
      }
    }
    function goHome(){ setStarted(false); setReveal(false); setPaused(false); }

    // Players
    function addPlayer(){
      const n = newPlayerName.trim();
      if(!n) return;
      setPlayers(p => [...p, { id: Date.now(), name: n, score: 0 }]);
      setNewPlayerName("");
    }
    function bump(id, d){ setPlayers(ps => ps.map(p => p.id === id ? { ...p, score: p.score + d } : p)); }
    function rename(id, name){ setPlayers(ps => ps.map(p => p.id === id ? { ...p, name } : p)); }
    function removePlayer(id){ setPlayers(ps => ps.filter(p => p.id !== id)); }

    function onMusicFile(f){
      const url = URL.createObjectURL(f);
      setBgUrl(url); setBgPlaying(true);
      setTimeout(() => audioRef.current?.play().catch(()=>{}), 50);
    }

    const currentProblem = bank[order[index]];
    // Resolve image URL relative to the JSON URL
    function problemImageUrl(img){
      if(!img) return null;
      try {
        const u = new URL(img, loadedUrl || document.baseURI);
        return u.toString();
      } catch { return img; }
    }

    useEffect(() => {
      let canceled = false;
      const opts = {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true }
        ],
        throwOnError: false
      };
      function typeset() {
        if (canceled) return;
        if (window.renderMathInElement) {
          if (questionRef.current) window.renderMathInElement(questionRef.current, opts);
          if (answerRef.current) window.renderMathInElement(answerRef.current, opts);
        } else {
          setTimeout(typeset, 50);
        }
      }
      typeset();
      return () => { canceled = true; };
    }, [currentProblem, reveal, started]);

    return React.createElement("div", { className: "min-h-screen flex flex-col w-full text-white overflow-hidden" },
      // Header
      React.createElement("div", { className: "shrink-0 flex flex-wrap items-center justify-between gap-3 p-3 backdrop-blur-md bg-white/10 border-b border-white/20" },
        React.createElement("div", { className: "text-lg font-black tracking-wide drop-shadow-sm" }, "Face‑Off Stage · Hosted Multiplayer"),
        React.createElement("div", { className: "flex items-center gap-2 text-xs" },
          React.createElement("button", { className: "px-3 py-1 rounded-md bg-black/40 hover:bg-black/60",
            onClick: () => {
              if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
              else document.exitFullscreen?.();
            }}, document.fullscreenElement ? "Exit Fullscreen" : "Fullscreen"),
          React.createElement("div", { className: "hidden md:flex items-center gap-2 bg-black/30 rounded-md px-2 py-1" },
            React.createElement("span", null, "Q‑Time"),
            React.createElement("input", { type: "number", value: questionTime,
              onChange: (e) => setQuestionTime(Math.max(5, Number(e.target.value))),
              className: "w-16 px-2 py-0.5 rounded bg-white/80 text-black" }),
            React.createElement("span", null, "s")
          ),
          React.createElement("div", { className: "hidden md:flex items-center gap-2 bg-black/30 rounded-md px-2 py-1" },
            React.createElement("span", null, "Rounds"),
            React.createElement("input", { type: "number", min:1, max:999, value: rounds,
              onChange: (e) => setRounds(Math.max(1, Number(e.target.value) || 1)),
              className: "w-16 px-2 py-0.5 rounded bg-white/80 text-black" })
          ),
          // Music
          React.createElement("div", { className: "flex items-center gap-2 bg-black/30 rounded-md px-2 py-1" },
            React.createElement("label", { className: "cursor-pointer px-2 py-0.5 rounded bg-white/20 hover:bg-white/30" }, "Import Music",
              React.createElement("input", { type: "file", accept: "audio/*", className: "hidden",
                onChange: (e) => { const f = e.target.files?.[0]; if (f) onMusicFile(f); } })
            ),
            React.createElement("button", { className: "px-2 py-0.5 rounded bg-white/20 hover:bg-white/30",
              onClick: () => {
                if (!audioRef.current) return;
                if (bgPlaying) { audioRef.current.pause(); setBgPlaying(false); }
                else { audioRef.current.play().catch(() => {}); setBgPlaying(true); }
              }}, bgPlaying ? "Pause" : "Play"),
            React.createElement("label", { className: "flex items-center gap-1 text-[11px]" },
              React.createElement("input", { type: "checkbox", checked: bgLoop, onChange: (e) => setBgLoop(e.target.checked) }), " loop"
            ),
            React.createElement("input", { type: "range", min:0, max:1, step:0.01, value: bgVol, onChange: (e) => setBgVol(Number(e.target.value)) })
          ),
          React.createElement("audio", { ref: audioRef, src: bgUrl ?? undefined, loop: bgLoop, onEnded: () => setBgPlaying(false), style: { display: "none" } })
        )
      ),
      // Main grid
      React.createElement("div", { className: "flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[300px_1fr] gap-4 p-4" },
        // Leaderboard
        React.createElement("div", { className: "h-full min-h-0 bg-white/15 rounded-2xl p-4 shadow-xl border border-white/20 flex flex-col" },
          React.createElement("div", { className: "flex items-center justify-between mb-3" },
            React.createElement("h2", { className: "text-xl font-bold" }, "Leaderboard"),
            React.createElement("div", { className: "text-xs opacity-80" }, "Host‑managed")
          ),
          React.createElement("div", { className: "flex gap-2 mb-3" },
            React.createElement("input", { value: newPlayerName, onChange: (e)=>setNewPlayerName(e.target.value), placeholder: "Player name",
              className: "w-[92px] sm:w-[108px] px-3 py-2 rounded-xl bg-white/80 text-black flex-none" }),
            React.createElement("button", { onClick: addPlayer, className: "px-3 py-2 rounded-xl bg-emerald-400 text-black font-bold" }, "Add")
          ),
          React.createElement("div", { className: "flex-1 min-h-0 overflow-auto pr-1" },
            [...players].sort((a,b)=>b.score-a.score).map(p =>
              React.createElement("div", { key: p.id, className: "mb-2 p-2 rounded-xl bg-black/25 flex items-center gap-2" },
                React.createElement("input", { value: p.name, onChange:(e)=>rename(p.id, e.target.value),
                  className: "w-[92px] sm:w-[108px] px-2 py-1 rounded bg-white/80 text-black flex-none text-sm" }),
                React.createElement("div", { className: "w-12 text-center text-2xl font-black" }, p.score),
                React.createElement("div", { className: "flex gap-1" },
                  React.createElement("button", { onClick: ()=>bump(p.id,+1), className: "px-2 py-1 rounded bg-emerald-400 text-black font-bold" }, "+1"),
                  React.createElement("button", { onClick: ()=>bump(p.id,-1), className: "px-2 py-1 rounded bg-rose-400 text-black font-bold" }, "−1"),
                  React.createElement("button", { onClick: ()=>removePlayer(p.id), className: "px-2 py-1 rounded bg-black/40" }, "✕")
                )
              )
            ),
            players.length===0 && React.createElement("div", { className: "text-sm opacity-80" }, "Add players to begin. Scores can be adjusted in real time.")
          )
        ),
        // Center Stage
        React.createElement("div", { className: "h-full min-h-0 grid grid-rows-[auto_1fr_auto] gap-4" },
          // Controls
          React.createElement("div", { className: "flex flex-wrap items-center justify-between gap-3 bg-white/15 rounded-2xl p-3 shadow-xl border border-white/20" },
            React.createElement("div", { className: "flex items-center gap-3" },
              React.createElement("div", { className: "text-sm opacity-80" }, "Round"),
              React.createElement("div", { className: "text-3xl font-black" }, Math.min(index+1, rounds), " / ", rounds)
            ),
            React.createElement("div", { className: "flex items-center gap-2" },
              React.createElement("div", { className: `px-3 py-1 rounded-full ${paused ? "bg-amber-300 text-black" : "bg-black/40"}` }, paused ? "Paused" : ("Time: " + timeLeft + "s")),
              React.createElement("button", { onClick: ()=>setPaused(p=>!p), className: "px-3 py-2 rounded-xl bg-white/20 hover:bg-white/30 font-bold" }, paused ? "Resume Timer" : "Pause Timer"),
              React.createElement("button", { onClick: resetTimer, className: "px-3 py-2 rounded-xl bg-white/20 hover:bg-white/30" }, "Reset"),
              !started
                ? React.createElement("button", { onClick: startGame, className: "px-4 py-2 rounded-xl bg-black/70 hover:bg-black/80 font-bold" }, "▶ Start")
                : React.createElement("button", { onClick: nextQuestion, className: "px-4 py-2 rounded-xl bg-black/70 hover:bg-black/80 font-bold" }, "Next Question"),
              React.createElement("input", { type: "number", min: 1, max: rounds, value: gotoValue, onChange: (e)=>setGotoValue(e.target.value), placeholder: "#", className: "w-16 px-2 py-1 rounded bg-white/80 text-black text-sm" }),
              React.createElement("button", { onClick: gotoQuestion, className: "px-3 py-2 rounded-xl bg-white/20 hover:bg-white/30 font-bold" }, "Go"),
              React.createElement("label", { className: "text-sm opacity-80" }, "Font"),
              React.createElement("input", { type: "number", min: 16, max: 72, value: fontSize, onChange: (e)=>setFontSize(Number(e.target.value)), className: "w-16 px-2 py-1 rounded bg-white/80 text-black text-sm" })
            )
          ),
          // Question card
          React.createElement("div", { className: "relative bg-white/15 rounded-3xl p-6 pt-9 shadow-2xl border border-white/20 overflow-auto" },
            React.createElement("div", { className: "absolute top-2 left-4 px-3 py-1 rounded-full text-xs bg-black/50" }, "Question #", started ? (currentProblem?.id ?? "—") : "—"),
            started && React.createElement("div", { className: "absolute top-2 right-4" },
              React.createElement("button", { onClick: ()=>setReveal(r=>!r), className: "px-3 py-1 rounded-full text-xs bg-emerald-400 text-black font-bold border border-emerald-900/20 shadow" },
                reveal ? "Hide Answer" : "Reveal Answer")
            ),
            React.createElement("div", {
              className: "font-bold leading-snug drop-shadow-sm",
              style: { fontSize: fontSize + "px" },
              ref: questionRef
            },
              started ? (currentProblem?.q ?? "Load question_bank.json to begin.") : "Press Start to reveal question."
            ),
            started && currentProblem?.image && React.createElement("div", { className: "mt-4" },
              React.createElement("img", { src: problemImageUrl(currentProblem.image), alt: "diagram", className: "max-w-full rounded-xl border border-white/30" })
            ),
            started && reveal && React.createElement("div", { className: "mt-4 p-3 rounded-2xl bg-emerald-400/20 border border-emerald-300/40" },
              React.createElement("div", { className: "text-sm opacity-80" }, "Answer"),
              React.createElement("div", { className: "font-extrabold text-emerald-200", style: { fontSize: Math.round(fontSize * 0.66) + "px" }, ref: answerRef }, String(currentProblem?.answer ?? ""))
            ),
            started && React.createElement("div", { className: "mt-6 w-full flex justify-center" },
              React.createElement("button", { onClick: goHome, className: "px-5 py-2 rounded-2xl bg-white/20 hover:bg-white/30 border border-white/30" }, "⟵ Home")
            )
          ),
          // Host Tools (inactive) — set selector
          !started && React.createElement("div", { className: "bg-white/15 rounded-2xl p-4 shadow-xl border border-white/20 space-y-3" },
            React.createElement("h3", { className: "font-bold" }, "Problem Sets (from question_bank.json)"),
            React.createElement("div", { className: "flex items-center gap-2 flex-wrap" },
              React.createElement("label", { className: "text-sm opacity-90" }, "Active Set"),
              React.createElement("select", { value: activeSetIdx, onChange: (e)=>setActiveSetIdx(Number(e.target.value)), className: "px-2 py-1 rounded bg-white/80 text-black" },
                sets.map((s, i) => React.createElement("option", { key: i, value: i }, `${s.name} (${s.problems.length})`))
              ),
              React.createElement("button", { onClick: ()=>setOrder(shuffle([...Array(bank.length).keys()])), className: "px-3 py-1 rounded bg-white/20 hover:bg-white/30" }, "Shuffle"),
              React.createElement("button", { onClick: ()=>setOrder([...Array(bank.length).keys()]), className: "px-3 py-1 rounded bg-white/20 hover:bg-white/30" }, "In Order")
            ),
            React.createElement("p", { className: "text-xs opacity-80" },
              "This page auto-loads ", React.createElement("code", null, "question_bank.json"), " from the same folder. ",
              "That file should list the JSON files for each problem set. ",
              "Each set file provides a ", React.createElement("code", null, "name"), " and its ", React.createElement("code", null, "problems"), ". ",
              "Each problem supports an optional ", React.createElement("code", null, "image"), " field (filename relative to the JSON)."
            )
          )
        )
      ),
      // Footer
      React.createElement("div", { className: "fixed bottom-2 left-1/2 -translate-x-1/2 text-[10px] opacity-70 text-center" },
        "Hosted on static site • Timer • Leaderboard • Images supported via JSON"
      )
    );
  }

  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(React.createElement(App));
})();