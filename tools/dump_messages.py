import json, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path
from tqdm import tqdm

DB_PATH = Path("persist") / "tinymod.db"

def _display_name(username: str, payload: dict) -> str:
  nick = (payload.get("member") or {}).get("nick")
  if nick: return nick
  author = payload.get("author") or {}
  return author.get("global_name") or author.get("username") or username

def dump_messages(db_path: Path, out_dir: Path, progress: bool = False) -> tuple[int, int]:
  """Dump messages from db_path to out_dir as JSONL files split by UTC date.
  Folds create/update/delete events into a single final-state row per message id:
  updates overwrite content, any delete drops the message. Returns
  (num_messages_written, num_date_files_written)."""
  out_dir.mkdir(parents=True, exist_ok=True)

  with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
    rows = conn.execute(
      "SELECT timestamp, username, content, json, action FROM logging_messages ORDER BY timestamp"
    ).fetchall()

  messages: dict[str, dict] = {}
  iter_events = tqdm(rows, desc="events") if progress else rows
  for ts, username, content, payload_raw, action in iter_events:
    try:
      payload = json.loads(payload_raw)
    except (json.JSONDecodeError, TypeError):
      continue
    msg_id = payload.get("id")
    if msg_id is None: continue

    if action == "delete":
      messages[msg_id] = {"deleted": True}
      continue
    if messages.get(msg_id, {}).get("deleted"): continue

    existing = messages.get(msg_id)
    if existing is None:
      messages[msg_id] = {"ts": ts, "username": username, "content": content, "payload": payload, "deleted": False}
    else:
      existing["content"] = content
      existing["username"] = username
      existing["payload"] = payload

  final = sorted((m for m in messages.values() if not m["deleted"] and m["content"]), key=lambda m: m["ts"])

  current_date, f, num_files = None, None, 0
  iter_final = tqdm(final, desc="writing") if progress else final
  try:
    for m in iter_final:
      date = datetime.fromtimestamp(m["ts"], tz=timezone.utc).strftime("%Y-%m-%d")
      if date != current_date:
        if f is not None: f.close()
        f = open(out_dir / f"{date}.jsonl", "w")
        current_date = date
        num_files += 1
      f.write(json.dumps({"timestamp": m["ts"], "display_name": _display_name(m["username"], m["payload"]), "content": m["content"]}) + "\n")
  finally:
    if f is not None: f.close()

  return len(final), num_files

if __name__ == "__main__":
  out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("messages")
  num_messages, num_files = dump_messages(DB_PATH, out, progress=True)
  print(f"wrote {num_messages} messages across {num_files} files to {out}")
