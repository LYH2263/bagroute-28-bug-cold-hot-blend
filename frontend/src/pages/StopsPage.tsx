import { useEffect, useState } from "react";
import { api } from "../api/client";
type S = { id: number; route_id: number; seq: number; name: string; weight_kg: number; volume_l: number; is_cold: boolean };
type R = { id: number; name: string };
export default function StopsPage() {
  const [routes, setRoutes] = useState<R[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [rows, setRows] = useState<S[]>([]);
  const [err, setErr] = useState("");
  useEffect(() => { api<R[]>("/routes").then(r => { setRoutes(r); if (r[0]) setRid(r[0].id); }); }, []);
  useEffect(() => {
    if (rid === "") return;
    api<S[]>(`/stops?route_id=${rid}`).then(setRows);
  }, [rid]);
  async function toggleCold(s: S) {
    setErr("");
    try {
      const updated = await api<S>(`/stops/${s.id}/cold`, {
        method: "PATCH",
        body: JSON.stringify({ is_cold: !s.is_cold }),
      });
      setRows(rs => rs.map(x => (x.id === updated.id ? updated : x)));
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>订户点</h2>
    <div className="toolbar">
      <select value={rid} onChange={e => setRid(Number(e.target.value))}>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <span className="hint">点击站点卡片可切换冷链标记</span>
    </div>
    <div className="route-strip">
      {rows.map(s => (
        <button
          className={"stop-chip" + (s.is_cold ? " stop-chip--cold" : "")}
          key={s.id}
          onClick={() => toggleCold(s)}
          title={s.is_cold ? "冷链站（点击取消）" : "普通站（点击标记为冷链）"}
        >
          <span className="seq">#{s.seq}</span>
          <strong>{s.name}</strong>
          <span className="mono">{s.weight_kg}kg · {s.volume_l}L</span>
          <span className={"cold-flag" + (s.is_cold ? " cold-flag--on" : "")}>{s.is_cold ? "❄ 冷链" : "常温"}</span>
        </button>
      ))}
    </div>
    {err && <div className="err">{err}</div>}
  </>);
}
