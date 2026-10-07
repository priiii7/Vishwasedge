import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { DocumentRecord, QueryResponse } from "../types";

export function useLogin() {
  return useMutation({
    mutationFn: async (payload: { username: string; password: string }) => {
      const { data } = await apiClient.post("/api/v1/auth/login", payload);
      return data as { access_token: string; role: string };
    },
  });
}

export function useSubmitQuery() {
  return useMutation({
    mutationFn: async (payload: {
      query: string;
      context?: Record<string, unknown>;
      maxDocs?: number;
      includeExplanation?: boolean;
    }) => {
      const { data } = await apiClient.post("/api/v1/query", {
        query: payload.query,
        context: payload.context ?? {},
        options: {
          stream: false,
          include_explanation: payload.includeExplanation ?? true,
          max_docs: payload.maxDocs ?? 5,
        },
      });
      return data as QueryResponse;
    },
  });
}

export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await apiClient.get("/api/v1/documents/list");
      return data as DocumentRecord[];
    },
    refetchInterval: 5000,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("source", file.name);
      const { data } = await apiClient.post("/api/v1/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useSystemModels() {
  return useQuery({
    queryKey: ["system-models"],
    queryFn: async () => {
      const { data } = await apiClient.get("/api/v1/system/models");
      return data as Array<{ name: string; role: string; active: boolean; detail: string }>;
    },
    staleTime: 30000,
  });
}
