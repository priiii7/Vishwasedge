import { useState } from "react";
import { Lock, ShieldCheck, User } from "lucide-react";
import { useLogin } from "../api/queries";
import { useChatStore } from "../stores/chatStore";

export function LoginForm() {
  const [username, setUsername] = useState("operator");
  const [password, setPassword] = useState("changeme123");
  const login = useLogin();
  const setAuth = useChatStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await login.mutateAsync({ username, password });
      setAuth({ token: result.access_token, username, role: result.role });
    } catch {
      // error surfaced via login.isError below
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-lg dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-6 flex flex-col items-center gap-2">
          <ShieldCheck className="h-10 w-10 text-indigo-600" />
          <h1 className="text-xl font-bold">VishwasEdge</h1>
          <p className="text-center text-xs text-slate-400">Trustworthy Edge-Native Multi-Agent RAG</p>
        </div>

        <label className="mb-3 flex items-center gap-2 rounded-xl border border-slate-300 px-3 py-2 dark:border-slate-700">
          <User className="h-4 w-4 text-slate-400" />
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full bg-transparent text-sm outline-none"
            placeholder="Username"
          />
        </label>

        <label className="mb-4 flex items-center gap-2 rounded-xl border border-slate-300 px-3 py-2 dark:border-slate-700">
          <Lock className="h-4 w-4 text-slate-400" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-transparent text-sm outline-none"
            placeholder="Password"
          />
        </label>

        {login.isError && (
          <p className="mb-3 text-xs text-red-500">Login failed — check credentials or backend status.</p>
        )}

        <button
          type="submit"
          disabled={login.isPending}
          className="w-full rounded-xl bg-indigo-600 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {login.isPending ? "Signing in…" : "Sign in"}
        </button>

        <p className="mt-4 text-center text-[11px] text-slate-400">
          Default: operator / changeme123 (seeded on first backend start)
        </p>
      </form>
    </div>
  );
}
