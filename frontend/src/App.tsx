import { useEffect } from "react";
import { LogOut, Moon, ShieldCheck, Sun } from "lucide-react";
import { ChatInterface } from "./components/ChatInterface";
import { DocumentPanel } from "./components/DocumentPanel";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { LoginForm } from "./components/LoginForm";
import { useChatStore } from "./stores/chatStore";

export default function App() {
  const { auth, logout, theme, toggleTheme } = useChatStore();

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  if (!auth.token) {
    return (
      <ErrorBoundary>
        <LoginForm />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className="flex h-screen flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-indigo-600" />
            <span className="font-bold">VishwasEdge</span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500 dark:bg-slate-800">
              {auth.username} · {auth.role}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={toggleTheme} className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800">
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <button onClick={logout} className="flex items-center gap-1.5 rounded-lg p-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800">
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </div>
        </header>

        <main className="grid flex-1 grid-cols-1 overflow-hidden md:grid-cols-[280px_1fr]">
          <aside className="hidden overflow-hidden border-r border-slate-200 dark:border-slate-800 md:block">
            <ErrorBoundary>
              <DocumentPanel />
            </ErrorBoundary>
          </aside>
          <section className="overflow-hidden">
            <ErrorBoundary>
              <ChatInterface />
            </ErrorBoundary>
          </section>
        </main>
      </div>
    </ErrorBoundary>
  );
}
