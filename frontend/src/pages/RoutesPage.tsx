import { useEffect, useState } from "react";
import { api } from "../api/client";
type R = { id: number; name: string; max_weight_kg: number; max_volume_l: number; max_cold_volume_l: number };
export default function RoutesPage() {
  const [rows, setRows] = useState<R[]>([]);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [savedId, setSavedId] = useState<number | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api<R[]>("/routes").then(rs => {
      setRows(rs);
      setDrafts(Object.fromEntries(rs.map(r => [r.id, String(r.max_cold_volume_l)])));
    });
  }, []);
  async function saveCold(r: R) {
    setErr(""); setSavedId(null);
    const val = Number(drafts[r.id]);
    if (!(val > 0)) { setErr("冷链体积上限必须为正数"); return; }
    if (val > r.max_volume_l) { setErr("冷链体积上限应严于（不大于）普通体积上限"); return; }
    try {
      const updated = await api<R>(`/routes/${r.id}`, {
        method: "PATCH",
        body: JSON.stringify({ max_cold_volume_l: val }),
      });
      setRows(rs => rs.map(x => (x.id === updated.id ? updated : x)));
      setSavedId(r.id);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>路线</h2>
    <table className="table"><thead><tr><th>名称</th><th>重量上限 kg</th><th>体积上限 L</th><th>冷链体积上限 L</th><th></th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.id}>
      <td>{r.name}</td>
      <td className="mono">{r.max_weight_kg}</td>
      <td className="mono">{r.max_volume_l}</td>
      <td className="mono">
        <input
          className="cold-input"
          type="number" step="0.1" min="0"
          value={drafts[r.id] ?? r.max_cold_volume_l}
          onChange={e => setDrafts(d => ({ ...d, [r.id]: e.target.value }))}
          style={{ width: "86px" }}
        />
      </td>
      <td>
        <button onClick={() => saveCold(r)}>保存冷链上限</button>
        {savedId === r.id && <span className="ok" style={{ marginLeft: ".5rem" }}>已保存</span>}
      </td>
    </tr>)}
      {!rows.length && <tr><td colSpan={5}>暂无路线</td></tr>}
    </tbody></table>
    {err && <div className="err">{err}</div>}
  </>);
}
