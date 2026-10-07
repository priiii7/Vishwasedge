import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthState, ChatMessage } from "../types";

interface ChatStore {
  auth: AuthState;
  setAuth: (auth: AuthState) => void;
  logout: () => void;

  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  updateLastMessage: (partial: Partial<ChatMessage>) => void;
  clearMessages: () => void;

  activeExplanationId: string | null;
  setActiveExplanationId: (id: string | null) => void;

  theme: "light" | "dark";
  toggleTheme: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      auth: { token: null, username: null, role: null },
      setAuth: (auth) => set({ auth }),
      logout: () => set({ auth: { token: null, username: null, role: null } }),

      messages: [],
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      updateLastMessage: (partial) =>
        set((state) => {
          if (state.messages.length === 0) return state;
          const messages = [...state.messages];
          messages[messages.length - 1] = { ...messages[messages.length - 1], ...partial };
          return { messages };
        }),
      clearMessages: () => set({ messages: [] }),

      activeExplanationId: null,
      setActiveExplanationId: (id) => set({ activeExplanationId: id }),

      theme: "dark",
      toggleTheme: () => set((state) => ({ theme: state.theme === "dark" ? "light" : "dark" })),
    }),
    {
      name: "vishwasedge-store",
      partialize: (state) => ({ auth: state.auth, theme: state.theme }),
    }
  )
);
